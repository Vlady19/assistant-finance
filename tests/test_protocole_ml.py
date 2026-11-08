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
        r=json.loads((ROOT/'reports/protocole_ml.json').read_text())
        train=set(r['familles_train']); test=set(r['familles_test'])
        self.assertFalse(train & test)
        self.assertEqual(len(train),r['effectif_train'])
        self.assertEqual(len(test),r['effectif_test'])
        brut=pd.read_parquet(ROOT/'data/raw/scfp2022.parquet')
        df=brut[brut.y1.mod(10).eq(1) & brut.yy1.isin(train)]
        # Calcul pandas de référence, indépendant de preparer_donnees/BornerRatios.
        reference=np.array([df.age.mean(),(df.equity/df.fin).clip(0,1).mean(),
                            (12*df.liq/df.norminc).clip(0,24).mean(),df.levratio.clip(0,1).mean()])
        bundle=joblib.load(clustering.MODELE_PATH)
        np.testing.assert_allclose(bundle['pipeline'].named_steps['scaler'].mean_,reference)
    def test_inference_reference_distance_euclidienne(self):
        bundle=joblib.load(clustering.MODELE_PATH)
        m=bundle['pipeline'];s=m.named_steps['scaler'];k=m.named_steps['kmeans']
        point=np.array([62.,.43,2.7,.09])
        distances=np.sqrt((((point-s.mean_)/s.scale_-k.cluster_centers_)**2).sum(axis=1))
        r=clustering.comparer(observations())
        self.assertEqual(r.cluster,int(np.argmin(distances)))
        self.assertAlmostEqual(r.distance,float(distances.min()),places=10)
    def test_rejet_profil_extreme(self):
        r=clustering.comparer(observations(age=120,part_actions_actuelle=1,liquidites_mois_revenu=0,ratio_dette_actifs=1))
        self.assertEqual(r.statut,'hors_distribution')
        self.assertIsNone(r.cluster)

    def test_fichier_corrompu_annonce(self):
        import tempfile
        with tempfile.TemporaryDirectory() as dossier:
            chemin=Path(dossier)/'modele.joblib'
            chemin.write_bytes(b'ceci nest pas un modele')
            resultat=clustering.comparer(observations(),chemin)
        self.assertEqual(resultat.statut,'modele_indisponible')
        self.assertIsNone(resultat.cluster)
