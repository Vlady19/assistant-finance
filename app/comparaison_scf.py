"""Comparaison locale : montants compréhensibles → ratios → graphique descriptif.

On ne demande pas à l'utilisateur de calculer ses propres ratios. Les euros
restent locaux ; seuls des proportions et des mois de revenu sont comparés.
Les positions décrivent l'échantillon, sans pondération de population.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .models import Profil
from .entrainement import preparer_donnees

SOURCE = Path(__file__).resolve().parents[1] / "data/raw/scfp2022.parquet"

class MontantsComparaison(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    age: float = Field(ge=18, le=120)
    epargne_totale_eur: float = Field(gt=0)
    actions_eur: float = Field(ge=0)
    liquidites_eur: float = Field(ge=0)
    revenu_mensuel_eur: float = Field(gt=0)
    patrimoine_total_eur: float = Field(gt=0)
    dettes_eur: float = Field(ge=0)

    @model_validator(mode="after")
    def verifier_totaux(self):
        # Les liquidités et les actions font partie de l'épargne financière.
        # Les biens immobiliers font partie du patrimoine total, pas de celle-ci.
        if self.actions_eur + self.liquidites_eur > self.epargne_totale_eur + .01:
            raise ValueError("Le total des actions et de l'argent disponible ne peut pas dépasser votre épargne et vos placements.")
        if self.epargne_totale_eur > self.patrimoine_total_eur + .01:
            raise ValueError("La valeur totale de vos biens doit inclure votre épargne et vos placements.")
        return self

    def vers_profil(self, profil: Profil) -> Profil:
        donnees = profil.model_dump()
        donnees.update(age=self.age,
            part_actions_actuelle=self.actions_eur / self.epargne_totale_eur,
            liquidites_mois_revenu=self.liquidites_eur / self.revenu_mensuel_eur,
            ratio_dette_actifs=self.dettes_eur / self.patrimoine_total_eur)
        return Profil.model_validate(donnees)


def charger_echantillon(chemin: Path | None = None) -> pd.DataFrame:
    # Même population exploitable que le protocole ML, mais valeurs brutes :
    # le rang et la médiane ne sont pas calculés sur les valeurs plafonnées.
    brut = pd.read_parquet(chemin or SOURCE)
    _, observations, _ = preparer_donnees(brut)
    if observations.empty:
        raise ValueError("Aucun ménage exploitable dans les données de comparaison.")
    return observations


# Facteur d'affichage : les ratios deviennent des pourcentages lisibles.
INDICATEURS = [
    ("age", "age", "Âge", "ans", 1, 100),
    ("part_risquee", "part_actions_actuelle", "Part de votre épargne en actions", "%", 100, 100),
    ("coussin_mois", "liquidites_mois_revenu", "Argent disponible, en mois de revenu", "mois", 1, 24),
    ("levier", "ratio_dette_actifs", "Dettes par rapport à la valeur de vos biens", "%", 100, 100),
]


def positions(profil: Profil, echantillon: pd.DataFrame) -> list[dict]:
    lignes = []
    for colonne, champ, titre, unite, facteur, borne in INDICATEURS:
        valeur = getattr(profil, champ)
        if valeur is None:
            raise ValueError("Complétez les informations de comparaison avant de tracer le graphique.")
        valeurs = echantillon[colonne].to_numpy(dtype=float) * facteur
        if not len(valeurs) or not np.isfinite(valeurs).all():
            raise ValueError("Données de comparaison absentes ou non valides.")
        vous = valeur * facteur
        lignes.append(dict(colonne=colonne, titre=titre, unite=unite, vous=vous,
            mediane=float(np.median(valeurs)),
            part_inferieure_ou_egale=float(np.mean(valeurs <= vous) * 100),
            effectif=len(valeurs), facteur=facteur, borne=borne))
    return lignes


def graphique(profil: Profil, echantillon: pd.DataFrame):
    """Quatre histogrammes et deux repères. Aucun appel LLM, aucun entraînement.

    On regroupe uniquement la queue de distribution dans la dernière barre
    pour garder les graphiques lisibles. La valeur de l'utilisateur n'est
    jamais tronquée : l'axe s'élargit si elle dépasse la borne habituelle.
    """
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    fig = Figure(figsize=(11, 7.6), facecolor="#ffffff", layout="constrained")
    axes = fig.subplots(2, 2)
    lignes = positions(profil, echantillon)
    for ax, ligne in zip(axes.flat, lignes):
        valeurs = echantillon[ligne["colonne"]].to_numpy() * ligne["facteur"]
        borne = max(ligne["borne"], math.ceil(ligne["vous"] * 1.15), math.ceil(ligne["mediane"] * 1.15))
        # np.histogram inclut la borne droite dans la dernière barre.
        ax.hist(np.minimum(valeurs, borne), bins=np.linspace(0, borne, 21),
                color="#7194b4", edgecolor="white", linewidth=.6)
        ax.axvline(ligne["mediane"], color="#16736c", linestyle="--", linewidth=2, label="Médiane")
        ax.axvline(ligne["vous"], color="#d45613", linewidth=2.8, label="Vous")
        ax.set_xlim(-borne*.025, borne*1.025)
        ax.set_title(ligne["titre"], fontsize=11, fontweight="bold", loc="left", pad=30)
        ax.text(0, 1.04, f"Vous : {ligne['vous']:.1f} {ligne['unite']}  ·  Médiane : {ligne['mediane']:.1f} {ligne['unite']}",
                transform=ax.transAxes, fontsize=9, color="#38485a")
        ticks=np.linspace(0,borne,5)
        ax.set_xticks(ticks, [f"{v:g}" for v in ticks[:-1]] + [f"{borne:g}+"])
        ax.set_xlabel(ligne["unite"])
        ax.set_ylabel("Nombre de ménages", fontsize=9)
        ax.grid(axis="y", alpha=.18)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_axisbelow(True)
    fig.suptitle("Où vous situez-vous dans l'échantillon américain ?", fontsize=16, fontweight="bold")
    fig.legend(handles=[Line2D([0],[0],color="#d45613",lw=2.8,label="Vous"),
        Line2D([0],[0],color="#16736c",lw=2,ls="--",label="Médiane : la moitié des ménages de chaque côté")],
        loc="outside lower center", ncol=2, frameon=False)
    return fig
