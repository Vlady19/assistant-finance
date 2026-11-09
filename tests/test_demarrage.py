"""Teste le démarrage sans clé API, les erreurs de rédaction et les réponses de secours.
Les pannes et réponses du service sont simulées, sans appel API réel.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch
from app import validation, pipeline, conversation
from app.config import obtenir_client, ServiceIndisponible
from app.intents import Politique

class DemarrageTests(unittest.TestCase):
    def test_validation_active(self):
        # Accepter l'absence de garantie ; refuser un rendement chiffré, même si le même nombre est dans le dossier.
        self.assertTrue(validation.valider("Aucun rendement n’est garanti. " + validation.MENTION).valide)
        self.assertFalse(validation.valider("Un rendement de 15 %. " + validation.MENTION, "Horizon : 15 ans").valide)
    def test_api_absente(self):
        # Sans clé, la création du client doit lever l'erreur prévue par l'application.
        # Vider le cache évite de réutiliser un client créé avant la suppression simulée de la clé.
        obtenir_client.cache_clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaises(ServiceIndisponible): obtenir_client()
    def test_repli_api_redaction(self):
        # Une panne de rédaction doit déclencher le texte de secours, sans afficher le contexte technique.
        with patch("app.redaction.rediger", side_effect=ServiceIndisponible("indisponible")):
            texte, erreurs, repli = pipeline._rediger_et_valider(Politique.EXPLIQUER, "(sans objet)", "ETF ?")
        self.assertTrue(repli)
        self.assertNotIn("sans objet", texte)
    def test_reessai(self):
        # Après une première réponse interdite, une seconde réponse valide doit éviter le texte de secours.
        # La liste side_effect fournit une réponse différente à chacun des deux appels.
        with patch("app.redaction.rediger", side_effect=["7 %", "La diversification répartit les expositions. " + validation.MENTION]) as rediger:
            texte, erreurs, repli = pipeline._rediger_et_valider(Politique.EXPLIQUER, "", "ETF ?")
        self.assertEqual(rediger.call_count, 2)
        self.assertFalse(repli)
    def test_interface_sans_cle(self):
        # Sans clé API, l'interface doit s'ouvrir sans exception et proposer le champ de chat.
        from streamlit.testing.v1 import AppTest
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app_streamlit.py")).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.chat_input), 1)
