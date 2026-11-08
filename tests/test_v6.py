import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError
from app import clustering, pipeline, conversation, intents, validation
from app.models import Profil

def profil(**modifs):
    data = dict(montant_eur=10000, horizon_annees=15, tolerance_risque="prudent",
                epargne_precaution_mois=6, resident_francais=True)
    data.update(modifs)
    return Profil(**data)

def observations(**modifs):
    data = dict(age=62, part_actions_actuelle=0.43, liquidites_mois_revenu=2.7, ratio_dette_actifs=0.09)
    data.update(modifs)
    return profil(**data)

class ProfilTests(unittest.TestCase):
    def test_bornes_et_finitude(self):
        for champ, valeur in [('montant_eur',-1),('horizon_annees',0),('epargne_precaution_mois',-1),('age',17),('part_actions_actuelle',1.1),('ratio_dette_actifs',-0.1),('montant_eur',float('nan')),('horizon_annees',float('inf'))]:
            with self.subTest(champ=champ, valeur=valeur), self.assertRaises(ValidationError): profil(**{champ:valeur})
    def test_zero_conserve(self):
        resultat=conversation.fusionner(observations(), profil(epargne_precaution_mois=0, ratio_dette_actifs=0))
        self.assertEqual(resultat.epargne_precaution_mois,0)
        self.assertEqual(resultat.ratio_dette_actifs,0)
        self.assertEqual(resultat.age,62)
    def test_observations_optionnelles(self):
        self.assertTrue(conversation.est_complet(profil()))
        self.assertIsNone(profil().age)

class ClusteringTests(unittest.TestCase):
    def test_modele_reel(self):
        r=clustering.comparer(observations())
        self.assertEqual(r.statut,'utilise')
        self.assertIsInstance(r.cluster,int)
        self.assertIsNotNone(r.distance)
        self.assertEqual(len(r.modele_sha256),64)
    def test_incomplet_pas_de_defaut(self):
        r=clustering.comparer(profil())
        self.assertEqual(r.statut,'informations_manquantes')
        self.assertIsNone(r.cluster)
    def test_fichier_absent_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            r=clustering.comparer(observations(),Path(temp)/'absent.joblib')
        self.assertEqual(r.statut,'modele_indisponible')
        self.assertIsNone(r.cluster)
    def test_chemin_independant_cwd(self):
        avant=os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            self.assertEqual(clustering.comparer(observations()).statut,'utilise')
        finally: os.chdir(avant)
    def test_tolerance_ne_modifie_pas_segment(self):
        a=clustering.comparer(observations(tolerance_risque='prudent'))
        b=clustering.comparer(observations(tolerance_risque='dynamique'))
        self.assertEqual(a.cluster,b.cluster)
    def test_plafonnement_annonce(self):
        r=clustering.comparer(observations(liquidites_mois_revenu=30,ratio_dette_actifs=1.2))
        self.assertTrue(any('plafonnées' in a for a in r.avertissements))

class PipelineTests(unittest.TestCase):
    def test_calcul_independant(self):
        trace=pipeline.calculer(profil())
        self.assertEqual([r['montant_eur'] for r in trace['allocation_illustrative']],[7500,2500])
        self.assertEqual(sum(r['pourcentage'] for r in trace['allocation_illustrative']),100)
    def test_pas_actions_si_prerequis_absents(self):
        for p in [profil(horizon_annees=1),profil(epargne_precaution_mois=0)]:
            self.assertEqual(pipeline.calculer(p)['allocation_illustrative'],[])
    def test_integration_ml_pas_juste_module(self):
        r=pipeline.analyser_profil(observations())
        self.assertEqual(r.trace['clustering']['statut'],'utilise')
        self.assertIn('distance standardisée',r.dossier)
    def test_changement_sujet_pendant_collecte(self):
        c=intents.Classification(intent=intents.Intent.PEDAGOGIE,reformulation='ETF',justification='définition')
        with patch('app.intents.classer',return_value=c), patch('app.pipeline.extraire_profil') as extraire, patch('app.redaction.rediger',return_value='Un ETF est un fonds coté. '+validation.MENTION):
            r=pipeline.traiter('Un ETF, c’est quoi ?',conversation.profil_vide(),'Quel montant ?')
        self.assertEqual(r.intent,intents.Intent.PEDAGOGIE)
        self.assertEqual(r.derniere_question,'Quel montant ?')
        extraire.assert_not_called()
    def test_prix_indisponible(self):
        c=intents.Classification(intent=intents.Intent.DONNEES_MARCHE,reformulation='prix',justification='donnée actuelle')
        with patch('app.intents.classer',return_value=c), patch('app.redaction.rediger') as rediger:
            r=pipeline.traiter('Cours actuel ?',profil())
        self.assertIn('pas de source',r.texte)
        rediger.assert_not_called()
    def test_montants_visibles_meme_si_redaction_echoue(self):
        with patch('app.redaction.rediger',return_value='7 % de rendement garanti'):
            r=pipeline.analyser_profil(profil(),avec_llm=True)
        self.assertTrue(r.repli_utilise)
        self.assertIn('7 500,00',r.dossier)
        self.assertNotIn('7 %',r.texte)
