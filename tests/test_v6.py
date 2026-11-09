"""Teste le profil, les règles, le clustering et les principaux parcours du pipeline.
Les appels LLM sont simulés ; les tests de clustering chargent le modèle enregistré.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError
from app import clustering, pipeline, conversation, intents, validation
from app.models import Profil

def profil(**modifs):
    # Profil fictif de base ; modifs permet de changer seulement les champs utiles au test.
    data = dict(montant_eur=10000, horizon_annees=15, tolerance_risque="prudent",
                epargne_precaution_mois=6, resident_francais=True)
    data.update(modifs)
    return Profil(**data)

def observations(**modifs):
    # Ajoute les quatre observations SCF nécessaires au modèle de clustering.
    data = dict(age=62, part_actions_actuelle=0.43, liquidites_mois_revenu=2.7, ratio_dette_actifs=0.09)
    data.update(modifs)
    return profil(**data)

class ProfilTests(unittest.TestCase):
    def test_bornes_et_finitude(self):
        # Les valeurs hors limites, NaN et l'infini doivent être refusés par Pydantic.
        for champ, valeur in [('montant_eur',-1),('horizon_annees',0),('epargne_precaution_mois',-1),('age',17),('part_actions_actuelle',1.1),('ratio_dette_actifs',-0.1),('montant_eur',float('nan')),('horizon_annees',float('inf'))]:
            # subTest indique le champ en échec ; assertRaises attend ici un rejet, pas une réussite.
            with self.subTest(champ=champ, valeur=valeur), self.assertRaises(ValidationError): profil(**{champ:valeur})
    def test_zero_conserve(self):
        # Un zéro remplace l'ancienne valeur ; une donnée absente ne doit pas effacer l'âge.
        resultat=conversation.fusionner(observations(), profil(epargne_precaution_mois=0, ratio_dette_actifs=0))
        self.assertEqual(resultat.epargne_precaution_mois,0)
        self.assertEqual(resultat.ratio_dette_actifs,0)
        self.assertEqual(resultat.age,62)
    def test_observations_optionnelles(self):
        # Les cinq données principales suffisent à l'analyse, même sans âge ni observations SCF.
        self.assertTrue(conversation.est_complet(profil()))
        self.assertIsNone(profil().age)

class ClusteringTests(unittest.TestCase):
    def test_modele_reel(self):
        # Le vrai modèle sauvegardé doit fournir un groupe, une distance et son empreinte SHA-256.
        r=clustering.comparer(observations())
        self.assertEqual(r.statut,'utilise')
        self.assertIsInstance(r.cluster,int)
        self.assertIsNotNone(r.distance)
        self.assertEqual(len(r.modele_sha256),64)
    def test_incomplet_pas_de_defaut(self):
        # Sans observations SCF, aucun groupe ne doit être inventé par défaut.
        r=clustering.comparer(profil())
        self.assertEqual(r.statut,'informations_manquantes')
        self.assertIsNone(r.cluster)
    def test_fichier_absent_visible(self):
        # Un modèle absent doit produire un statut clair, sans groupe de remplacement.
        with tempfile.TemporaryDirectory() as temp:
            r=clustering.comparer(observations(),Path(temp)/'absent.joblib')
        self.assertEqual(r.statut,'modele_indisponible')
        self.assertIsNone(r.cluster)
    def test_chemin_independant_cwd(self):
        # Le modèle doit être trouvé même si le programme est lancé depuis un autre dossier.
        avant=os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            self.assertEqual(clustering.comparer(observations()).statut,'utilise')
        finally: os.chdir(avant)
    def test_tolerance_ne_modifie_pas_segment(self):
        # Changer le risque déclaré ne doit pas changer le groupe SCF : les données observées sont identiques.
        a=clustering.comparer(observations(tolerance_risque='prudent'))
        b=clustering.comparer(observations(tolerance_risque='dynamique'))
        self.assertEqual(a.cluster,b.cluster)
    def test_plafonnement_annonce(self):
        # Si les ratios dépassent les plafonds du modèle, le résultat doit le signaler.
        r=clustering.comparer(observations(liquidites_mois_revenu=30,ratio_dette_actifs=1.2))
        self.assertTrue(any('plafonnées' in a for a in r.avertissements))

class PipelineTests(unittest.TestCase):
    def test_calcul_independant(self):
        # Pour ce profil prudent : 7 500 € + 2 500 €, et des pourcentages qui totalisent 100.
        trace=pipeline.calculer(profil())
        self.assertEqual([r['montant_eur'] for r in trace['allocation_illustrative']],[7500,2500])
        self.assertEqual(sum(r['pourcentage'] for r in trace['allocation_illustrative']),100)
    def test_pas_actions_si_prerequis_absents(self):
        # Horizon trop court ou réserve insuffisante : aucune allocation ne doit être affichée.
        for p in [profil(horizon_annees=1),profil(epargne_precaution_mois=0)]:
            self.assertEqual(pipeline.calculer(p)['allocation_illustrative'],[])
    def test_integration_ml_pas_juste_module(self):
        # L'analyse complète doit appeler le modèle et inclure sa distance dans le dossier affiché.
        r=pipeline.analyser_profil(observations())
        self.assertEqual(r.trace['clustering']['statut'],'utilise')
        self.assertIn('distance standardisée',r.dossier)
    def test_changement_sujet_pendant_collecte(self):
        # Une question sur les ETF doit interrompre la collecte sans perdre la question en attente.
        c=intents.Classification(intent=intents.Intent.PEDAGOGIE,reformulation='ETF',justification='définition')
        # On simule le LLM ; extraire sert aussi à vérifier que l'extraction n'a pas été appelée.
        with patch('app.intents.classer',return_value=c), patch('app.pipeline.extraire_profil') as extraire, patch('app.redaction.rediger',return_value='Un ETF est un fonds coté. '+validation.MENTION):
            r=pipeline.traiter('Un ETF, c’est quoi ?',conversation.profil_vide(),'Quel montant ?')
        self.assertEqual(r.intent,intents.Intent.PEDAGOGIE)
        self.assertEqual(r.derniere_question,'Quel montant ?')
        extraire.assert_not_called()
    def test_prix_indisponible(self):
        # Sans source de marché, le système doit annoncer la limite sans demander au LLM de rédiger un cours.
        c=intents.Classification(intent=intents.Intent.DONNEES_MARCHE,reformulation='prix',justification='donnée actuelle')
        with patch('app.intents.classer',return_value=c), patch('app.redaction.rediger') as rediger:
            r=pipeline.traiter('Cours actuel ?',profil())
        self.assertIn('pas de source',r.texte)
        rediger.assert_not_called()
    def test_montants_visibles_meme_si_redaction_echoue(self):
        # Une rédaction interdite est remplacée, mais les montants Python restent visibles.
        with patch('app.redaction.rediger',return_value='7 % de rendement garanti'):
            r=pipeline.analyser_profil(profil(),avec_llm=True)
        self.assertTrue(r.repli_utilise)
        self.assertIn('7 500,00',r.dossier)
        self.assertNotIn('7 %',r.texte)
