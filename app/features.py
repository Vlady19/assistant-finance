"""La même préparation est appliquée à l'entraînement et à chaque prédiction."""
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

VARIABLES = ["age", "part_risquee", "coussin_mois", "levier"]

class BornerRatios(TransformerMixin, BaseEstimator):
    """Plafonds hérités de l'EDA : on les conserve et on les documente.

    Les valeurs absentes sont refusées en amont, jamais remplacées ici.
    Le plafonnement réduit l'effet des valeurs extrêmes sur KMeans.
    """
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        resultat = pd.DataFrame(X, columns=VARIABLES).copy()
        resultat["part_risquee"] = resultat["part_risquee"].clip(0, 1)
        resultat["coussin_mois"] = resultat["coussin_mois"].clip(0, 24)
        resultat["levier"] = resultat["levier"].clip(0, 1)
        return resultat
