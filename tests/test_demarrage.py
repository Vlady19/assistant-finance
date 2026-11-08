import os
import unittest
from pathlib import Path
from unittest.mock import patch
from app import validation, pipeline, conversation
from app.config import obtenir_client, ServiceIndisponible
from app.intents import Politique

class DemarrageTests(unittest.TestCase):
    def test_validation_active(self):
        self.assertTrue(validation.valider("Aucun rendement n’est garanti. " + validation.MENTION).valide)
        self.assertFalse(validation.valider("Un rendement de 15 %. " + validation.MENTION, "Horizon : 15 ans").valide)
    def test_api_absente(self):
        obtenir_client.cache_clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaises(ServiceIndisponible): obtenir_client()
    def test_repli_api_redaction(self):
        with patch("app.redaction.rediger", side_effect=ServiceIndisponible("indisponible")):
            texte, erreurs, repli = pipeline._rediger_et_valider(Politique.EXPLIQUER, "(sans objet)", "ETF ?")
        self.assertTrue(repli)
        self.assertNotIn("sans objet", texte)
    def test_reessai(self):
        with patch("app.redaction.rediger", side_effect=["7 %", "La diversification répartit les expositions. " + validation.MENTION]) as rediger:
            texte, erreurs, repli = pipeline._rediger_et_valider(Politique.EXPLIQUER, "", "ETF ?")
        self.assertEqual(rediger.call_count, 2)
        self.assertFalse(repli)
    def test_interface_sans_cle(self):
        from streamlit.testing.v1 import AppTest
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app_streamlit.py")).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.chat_input), 1)
