"""Teste les parcours Streamlit avec AppTest, sans ouvrir de navigateur.
Couvre les formulaires, la comparaison facultative, l'historique et les pannes simulées.
"""

import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from app import intents, validation
from test_v6 import observations
APP=Path(__file__).resolve().parents[1]/'app_streamlit.py'

class InterfaceTests(unittest.TestCase):
    def ouvrir(self):
        # Lance Streamlit dans son outil de test, sans navigateur.
        return AppTest.from_file(str(APP),default_timeout=30).run()
    def cliquer(self, app, label):
        # Après le clic, run rejoue l'application comme dans une vraie session Streamlit.
        next(b for b in app.button if b.label == label).click().run()
    def analyser(self, app):
        # Remplit le cas prudent de référence et lance son analyse locale.
        for champ,valeur in zip(app.number_input,[10000.,15.,6.]): champ.set_value(valeur)
        app.selectbox[0].select('prudent');app.selectbox[1].select('Oui')
        self.cliquer(app,'Analyser mon épargne')
    def remplir_comparaison(self, app):
        # Renseigne les montants fictifs dans les champs SCF repérés par leur clé.
        donnees={'age':35.,'epargne_totale_eur':20000.,'actions_eur':4000.,'liquidites_eur':6000.,
                 'revenu_mensuel_eur':3000.,'patrimoine_total_eur':80000.,'dettes_eur':16000.}
        for nom,valeur in donnees.items():
            next(x for x in app.number_input if x.key=='scf_'+nom).set_value(valeur)
    def test_comparaison_facultative_apres_analyse(self):
        # La comparaison doit être proposée après l'analyse, puis ignorée sans lancer le modèle si l'utilisateur refuse.
        app=self.ouvrir()
        self.assertEqual(len(app.number_input),3)
        self.assertNotIn('Oui, voir où je me situe',[b.label for b in app.button])
        # Ce faux modèle sert d'espion : assert_not_called vérifie qu'aucun clustering n'a été demandé.
        with patch('app.clustering.comparer') as comparer:
            self.analyser(app)
            self.assertEqual(len(app.exception),0)
            self.assertEqual(app.session_state['messages'][-1]['reponse']['trace']['clustering']['statut'],'non_demandee')
            self.cliquer(app,'Pas maintenant')
            comparer.assert_not_called()
        self.assertEqual(app.session_state['scf_choix'],False)
        self.assertEqual(len(app.number_input),3)
    def test_formulaire_euros_graphique_et_ml(self):
        # Le formulaire SCF doit calculer les ratios, appeler le modèle et montrer le graphique sans passer par le LLM.
        app=self.ouvrir();self.analyser(app);self.cliquer(app,'Oui, voir où je me situe')
        self.remplir_comparaison(app)
        # La comparaison doit rester locale : le rédacteur LLM ne doit jamais être appelé ici.
        with patch('app.redaction.rediger') as rediger:
            self.cliquer(app,'Afficher ma comparaison')
            rediger.assert_not_called()
        self.assertEqual(len(app.exception),0)
        resultat=app.session_state['scf_resultat']
        self.assertEqual(resultat['profil']['liquidites_mois_revenu'],2.)
        self.assertEqual(resultat['profil']['ratio_dette_actifs'],.2)
        self.assertEqual(resultat['modele']['statut'],'utilise')
        # Les montants du formulaire local ne sont pas ajoutés à la mémoire LLM.
        self.assertIsNone(app.session_state['profil'].liquidites_mois_revenu)
        self.assertIn('Votre position, en un coup d’œil'.replace('’',"'"),
                      ' '.join(x.value for x in app.subheader).replace('’',"'"))
        self.assertGreater(len(app.get('image')),0)
        # Recommencer doit ensuite effacer les messages et les informations du profil.
        self.cliquer(app,'Recommencer')
        self.assertEqual(app.session_state['messages'],[])
        self.assertIsNone(app.session_state['profil'].age)
    def test_formulaire_incomplet(self):
        # Un formulaire incomplet doit afficher un avertissement, sans créer de réponse ni planter.
        app=self.ouvrir();self.cliquer(app,'Analyser mon épargne')
        self.assertEqual(len(app.exception),0)
        self.assertGreater(len(app.warning),0)
        self.assertEqual(app.session_state['messages'],[])
    def test_comparaison_invalide_efface_resultat_precedent(self):
        # Une nouvelle saisie invalide doit effacer l'ancien résultat, pour ne pas le faire passer pour un résultat à jour.
        app=self.ouvrir();self.analyser(app);self.cliquer(app,'Oui, voir où je me situe')
        self.remplir_comparaison(app);self.cliquer(app,'Afficher ma comparaison')
        # Un revenu nul doit invalider la comparaison et effacer l'ancien résultat.
        next(x for x in app.number_input if x.key=='scf_revenu_mensuel_eur').set_value(0.)
        self.cliquer(app,'Afficher ma comparaison')
        self.assertIsNone(app.session_state['scf_resultat'])
        self.assertGreater(len(app.warning),0)
    def test_chat_complet_et_historique_sans_comparaison_automatique(self):
        # Un profil complet dans le chat ne doit pas lancer le SCF ; un nouvel affichage ne doit pas doubler l'historique.
        app=self.ouvrir()
        classe=intents.Classification(intent=intents.Intent.ALLOCATION,reformulation='capital',justification='allocation')
        with patch('app.intents.classer',return_value=classe), patch('app.pipeline.extraire_profil',return_value=observations()), patch('app.redaction.rediger',return_value='Voici les règles du projet. '+validation.MENTION), patch('app.clustering.comparer') as comparer:
            app.chat_input[0].set_value('Mon profil complet').run()
            comparer.assert_not_called()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.session_state['messages']),2)
        self.assertEqual(app.session_state['messages'][-1]['reponse']['trace']['clustering']['statut'],'non_demandee')
        app.run();self.assertEqual(len(app.session_state['messages']),2)
    def test_erreur_api_sans_perte_profil(self):
        # Une panne de classification doit afficher un message d'indisponibilité, sans exception dans l'interface.
        from app.config import ServiceIndisponible
        app=self.ouvrir()
        with patch('app.intents.classer',side_effect=ServiceIndisponible('Service temporairement indisponible')):
            app.chat_input[0].set_value('Bonjour').run()
        self.assertEqual(len(app.exception),0)
        self.assertIn('indisponible',app.session_state['messages'][-1]['reponse']['texte'])
