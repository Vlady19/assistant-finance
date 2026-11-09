"""Compare un profil au pipeline K-Means enregistré et calcule sa distance.
Signale les observations manquantes, le modèle indisponible et les profils trop éloignés.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import hashlib
import pickle
import joblib
import numpy as np
import pandas as pd
from .features import VARIABLES
from .models import Profil

MODELE_PATH = Path(__file__).resolve().parents[1] / "models" / "segmentation.joblib"
CHAMPS = ["age", "part_actions_actuelle", "liquidites_mois_revenu", "ratio_dette_actifs"]

@dataclass
class ResultatClustering:
    """Statut de comparaison, groupe éventuel, distance et informations de traçabilité."""
    statut: str
    explication: str
    cluster: int | None = None
    distance: float | None = None
    modele_sha256: str | None = None
    entrees: dict = field(default_factory=dict)
    moyennes_segment: dict = field(default_factory=dict)
    avertissements: list[str] = field(default_factory=list)
    def to_dict(self):
        return asdict(self)

def comparer(profil: Profil, chemin: Path | None = None) -> ResultatClustering:
    """Charge le pipeline, attribue un groupe et contrôle le seuil de distance.
    Renvoie un statut explicite si les données ou le modèle ne permettent pas la comparaison.
    """
    manquants = [c for c in CHAMPS if getattr(profil, c) is None]
    if manquants:
        return ResultatClustering("informations_manquantes",
            "Comparaison SCF non calculée. Observations à fournir : " + ", ".join(manquants))
    chemin = Path(chemin or MODELE_PATH)
    try:
        # Charger uniquement nos artefacts locaux de confiance : joblib n'est
        # pas un format adapté à l'import libre de modèles envoyés par un tiers.
        contenu = chemin.read_bytes()
        import io
        bundle = joblib.load(io.BytesIO(contenu))
        modele = bundle["pipeline"]
        entrees = dict(zip(VARIABLES, [getattr(profil, c) for c in CHAMPS]))
        X = pd.DataFrame([entrees], columns=VARIABLES)
        cluster = int(modele.predict(X)[0])  # vrai appel KMeans, pas une table de secours
        # La distance est mesurée après bornage et standardisation du profil.
        distance = float(modele.transform(X)[0, cluster])
        centres = modele.named_steps["scaler"].inverse_transform(modele.named_steps["kmeans"].cluster_centers_)
        moyennes = dict(zip(VARIABLES, map(float, centres[cluster])))
        seuil = bundle.get("distance_max")
        avertissements = ["SCF 2022 : ménages américains ; comparaison descriptive, non recommandation."]
        if profil.liquidites_mois_revenu > 24 or profil.ratio_dette_actifs > 1:
            avertissements.append("Valeurs extrêmes plafonnées comme à l'entraînement : liquidités à 24, dette/actifs à 1.")
        # Au-delà du seuil appris sur train, l'attribution est écartée sans groupe de secours.
        if seuil is not None and distance > seuil:
            return ResultatClustering("hors_distribution", "Profil éloigné des observations d'entraînement : attribution non retenue.",
                distance=distance, modele_sha256=hashlib.sha256(contenu).hexdigest(), entrees=entrees, avertissements=avertissements)
        return ResultatClustering("utilise", "Segment obtenu par le pipeline SCF sauvegardé.",
            cluster, distance, hashlib.sha256(contenu).hexdigest(), entrees, moyennes, avertissements)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, EOFError, ImportError, IndexError, pickle.UnpicklingError) as erreur:
        return ResultatClustering("modele_indisponible",
            "Comparaison ML indisponible (" + type(erreur).__name__ + "). Reconstruisez le modèle ; aucune segmentation de remplacement n'a été utilisée.")
