"""Teste la séparation train/test, le scaler et les distances du modèle enregistré.
Vérifie aussi l'abstention sur profil extrême et le signalement d'un modèle corrompu.
"""

import json
import unittest
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from app import clustering
from test_v6 import observations
ROOT=Path(__file__).resolve().parents[1]

class ProtocoleMLTests(unittest.TestCase):
    def test_familles_separees_et_scaler_train_seul(self):
        # Aucune famille commune au train et au test ; les moyennes du scaler doivent venir du train seul.
        r=json.loads((ROOT/'reports/protocole_ml.json').read_text())
        train=set(r['familles_train']); test=set(r['familles_test'])
        # L'intersection doit être vide : une famille ne doit jamais servir dans les deux lots.
        self.assertFalse(train & test)
        self.assertEqual(len(train),r['effectif_train'])
        self.assertEqual(len(test),r['effectif_test'])
        brut=pd.read_parquet(ROOT/'data/raw/scfp2022.parquet')
        # Le dernier chiffre de y1 sélectionne le premier implicat, une version des données complétées.
        df=brut[brut.y1.mod(10).eq(1) & brut.yy1.isin(train)]
        # Calcul pandas de référence, indépendant de preparer_donnees/BornerRatios.
        # On reprend les ratios et leurs plafonds sur les seules familles train, puis on calcule leurs moyennes.
        reference=np.array([df.age.mean(),(df.equity/df.fin).clip(0,1).mean(),
                            (12*df.liq/df.norminc).clip(0,24).mean(),df.levratio.clip(0,1).mean()])
        bundle=joblib.load(clustering.MODELE_PATH)
        np.testing.assert_allclose(bundle['pipeline'].named_steps['scaler'].mean_,reference)
    def test_inference_reference_distance_euclidienne(self):
        # Recalculer les distances avec NumPy pour vérifier le groupe et la distance renvoyés par l'application.
        bundle=joblib.load(clustering.MODELE_PATH)
        m=bundle['pipeline'];s=m.named_steps['scaler'];k=m.named_steps['kmeans']
        point=np.array([62.,.43,2.7,.09])
        # Standardiser le profil, puis calculer sa distance à chaque centre : racine de la somme des écarts au carré.
        distances=np.sqrt((((point-s.mean_)/s.scale_-k.cluster_centers_)**2).sum(axis=1))
        r=clustering.comparer(observations())
        # argmin donne le centre le plus proche ; la distance doit aussi coïncider à dix décimales.
        self.assertEqual(r.cluster,int(np.argmin(distances)))
        self.assertAlmostEqual(r.distance,float(distances.min()),places=10)
    def test_rejet_profil_extreme(self):
        # Un profil trop éloigné doit être déclaré hors distribution, sans groupe retenu.
        r=clustering.comparer(observations(age=120,part_actions_actuelle=1,liquidites_mois_revenu=0,ratio_dette_actifs=1))
        self.assertEqual(r.statut,'hors_distribution')
        self.assertIsNone(r.cluster)

    def test_fichier_corrompu_annonce(self):
        # Un fichier illisible doit être signalé comme modèle indisponible, sans faire planter l'appel.
        import tempfile
        with tempfile.TemporaryDirectory() as dossier:
            chemin=Path(dossier)/'modele.joblib'
            chemin.write_bytes(b'ceci nest pas un modele')
            resultat=clustering.comparer(observations(),chemin)
        self.assertEqual(resultat.statut,'modele_indisponible')
        self.assertIsNone(resultat.cluster)
