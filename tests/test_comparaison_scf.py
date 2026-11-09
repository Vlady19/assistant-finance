"""Teste les montants SCF, leurs ratios et les graphiques descriptifs.
Vérifie les saisies invalides, les ex æquo et les valeurs extrêmes avec des références connues.
"""

import unittest
import numpy as np
import pandas as pd
from pydantic import ValidationError
from app.comparaison_scf import MontantsComparaison, positions, graphique, charger_echantillon
from test_v6 import profil

def montants(**modifs):
    # Montants fictifs de référence : actions 20 %, liquidités 2 mois de revenu, dette/actifs 20 %.
    data=dict(age=35,epargne_totale_eur=20000,actions_eur=4000,liquidites_eur=6000,
              revenu_mensuel_eur=3000,patrimoine_total_eur=80000,dettes_eur=16000)
    data.update(modifs)
    return MontantsComparaison(**data)

class ComparaisonSCFTests(unittest.TestCase):
    def test_conversion_euros_sans_confusion_unites(self):
        # Convertir les euros en ratios sans confondre les mois de revenu et les mois de dépenses.
        p=montants().vers_profil(profil())
        self.assertEqual(p.liquidites_mois_revenu,2)
        self.assertEqual(p.part_actions_actuelle,.2)
        self.assertEqual(p.ratio_dette_actifs,.2)
        self.assertEqual(p.epargne_precaution_mois,6)
    def test_incoherence_totaux(self):
        # Refuser des actions + liquidités supérieures à l'épargne, ou des biens inférieurs à l'épargne.
        for modif in [dict(actions_eur=15000),dict(patrimoine_total_eur=10000)]:
            with self.subTest(modif=modif),self.assertRaises(ValidationError):montants(**modif)
    def test_zero_absence_actions_et_dettes(self):
        # Aucune action ou aucune dette donne bien un ratio nul, pas une information manquante.
        p=montants(actions_eur=0,dettes_eur=0).vers_profil(profil())
        self.assertEqual(p.part_actions_actuelle,0)
        self.assertEqual(p.ratio_dette_actifs,0)
    def test_denominateur_nul_et_non_fini(self):
        # Refuser les divisions par zéro et les valeurs invalides comme NaN.
        for champ in ['epargne_totale_eur','revenu_mensuel_eur','patrimoine_total_eur']:
            with self.subTest(champ=champ),self.assertRaises(ValidationError):montants(**{champ:0})
        with self.assertRaises(ValidationError):montants(actions_eur=float('nan'))
    def test_rang_reference_independante_et_ex_aequo(self):
        # Avec quatre ménages connus, vérifier le rang, les ex æquo et les médianes à la main.
        df=pd.DataFrame({'age':[20,30,40,50], 'part_risquee':[0,.2,.2,.8],
                         'coussin_mois':[0,1,2,100], 'levier':[0,.1,.2,5]})
        r=positions(montants().vers_profil(profil()),df)
        # Trois ménages sur quatre ont au plus 20 % d'actions : le rang attendu est donc 75 %, ex æquo inclus.
        self.assertEqual(r[1]['part_inferieure_ou_egale'],75)
        self.assertEqual(r[1]['mediane'],20)
        self.assertEqual(r[2]['mediane'],1.5)
    def test_graphiques_reperes_et_extreme_non_tronque(self):
        # Le graphique doit montrer les quatre variables, tous les ménages et le repère utilisateur même extrême.
        df=pd.DataFrame({'age':[20,30,40,50], 'part_risquee':[0,.2,.2,.8],
                         'coussin_mois':[0,1,2,100], 'levier':[0,.1,.2,5]})
        p=montants(revenu_mensuel_eur=100).vers_profil(profil())
        fig=graphique(p,df)
        self.assertEqual(len(fig.axes),4)
        # Le troisième graphique montre les liquidités ; son deuxième trait représente l'utilisateur.
        trait_vous=fig.axes[2].lines[1]
        # 6 000 € / 100 € de revenu = 60 mois : l'axe doit s'étendre pour montrer ce repère.
        self.assertEqual(trait_vous.get_xdata()[0],60)
        self.assertGreater(fig.axes[2].get_xlim()[1],60)
        for ax in fig.axes: self.assertEqual(sum(p.get_height() for p in ax.patches),4)
    def test_reference_reelle_et_non_plafonnee(self):
        # Les graphiques doivent utiliser les 4 532 ménages et les ratios bruts, sans les plafonds du clustering.
        df=charger_echantillon()
        self.assertEqual(len(df),4532)
        self.assertTrue(df.coussin_mois.max()>24)
        self.assertTrue(df.levier.max()>1)
