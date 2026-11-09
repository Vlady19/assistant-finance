"""Définit les quatre variables et leur bornage avant standardisation.
Le même transformateur est utilisé à l'entraînement et à l'inférence.
"""

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

VARIABLES = ["age", "part_risquee", "coussin_mois", "levier"]

class BornerRatios(TransformerMixin, BaseEstimator):
    """Plafonne les ratios SCF avant standardisation pour limiter les valeurs extrêmes.
    Les valeurs manquantes sont traitées en amont, sans imputation dans ce transformateur.
    """
    def fit(self, X, y=None):
        """Respecte l'interface scikit-learn ; les bornes sont fixes et ne sont pas apprises."""
        return self
    def transform(self, X):
        resultat = pd.DataFrame(X, columns=VARIABLES).copy()
        resultat["part_risquee"] = resultat["part_risquee"].clip(0, 1)
        resultat["coussin_mois"] = resultat["coussin_mois"].clip(0, 24)
        resultat["levier"] = resultat["levier"].clip(0, 1)
        return resultat
