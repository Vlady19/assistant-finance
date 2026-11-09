"""Teste les contrôles du texte et la séparation entre explication LLM et chiffres Python.
Vérifie notamment les garanties interdites et l'exclusion des causes SCF de l'allocation.
"""

import unittest
from unittest.mock import patch
from app import pipeline, validation
from test_v6 import observations

class RedactionTests(unittest.TestCase):
    def test_pas_de_causalite_scf_dans_redaction_regles(self):
        # Le rédacteur des règles ne doit pas recevoir l'âge ni le SCF comme justification de l'allocation.
        with patch('app.redaction.rediger',return_value='Le niveau retenu applique les règles du projet. '+validation.MENTION) as rediger:
            pipeline.analyser_profil(observations(),message='Mon âge est 62 ans',avec_llm=True)
        # Le faux rédacteur garde les arguments reçus : on contrôle ce que le pipeline lui a transmis.
        donnees=rediger.call_args.kwargs
        self.assertNotIn('age',donnees['dossier'])
        self.assertNotIn('62',donnees['message'])
        self.assertNotIn('SCF',donnees['dossier'])
    def test_chiffres_en_lettres(self):
        # Les nombres sont refusés dans la prose, qu'ils soient écrits en chiffres ou en lettres.
        for texte in ['Rendement de sept pour cent','Cela coûte trois euros','Le gain sera de 12 %']:
            self.assertFalse(validation.valider(texte+validation.MENTION).valide)
    def test_pas_de_garantie_positive(self):
        # Une promesse de rendement garanti doit être rejetée.
        self.assertFalse(validation.valider('Le rendement est garanti. '+validation.MENTION).valide)
    def test_chiffres_confies_au_rendu_python(self):
        # Refuser le rendement inventé, tout en conservant l'horizon réel dans le rendu Python.
        with patch('app.redaction.rediger',return_value='Le rendement attendu est de 15 %. '+validation.MENTION):
            r=pipeline.analyser_profil(observations(),avec_llm=True)
        self.assertTrue(r.repli_utilise)
        self.assertNotIn('rendement attendu est',r.texte)
        self.assertIn('15 ans',r.dossier)
