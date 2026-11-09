"""Définit le profil Pydantic commun au chat, aux formulaires et à l'inférence.
Valide les valeurs saisies et fournit les questions de collecte des informations principales.
"""


from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class Profil(BaseModel):
    """Données communes au chat, au formulaire et à l'inférence.
    Les cinq champs principaux sont requis mais acceptent None. Les observations
    SCF sont facultatives. Les contraintes portent sur les bornes et les valeurs finies.
    """

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    montant_eur: float | None = Field(
        ge=0,
        description=(
            "Capital ponctuel que la personne souhaite investir, en euros. "
            "Mettre 0 si la personne dit ne rien avoir à investir, par exemple "
            "'je n'ai pas d'argent', 'rien à investir' ou '0 euro'. "
            "Ne jamais remplacer 0 par une petite valeur positive. "
            "Un versement mensuel seul n'est pas un capital : laisser null. "
            "Convertir les formulations courantes : '10k' vaut 10000. "
            "null si aucun montant n'est mentionné."
        )
    )

    horizon_annees: float | None = Field(
        gt=0,
        description=(
            "Durée pendant laquelle la personne peut laisser cet argent "
            "investi, en années. null si non mentionnée. "
            "Attention : 'long terme' seul n'est pas un chiffre, donc null."
        )
    )

    tolerance_risque: Literal["prudent", "equilibre", "dynamique"] | None = Field(
        description=(
            "Niveau de risque que la personne dit accepter. "
            "Si elle répond par une lettre à la question à choix multiples : "
            "A -> prudent, B -> equilibre, C -> dynamique. "
            "Sinon, interpréter le langage naturel : 'peu de risque' ou "
            "'sécurisé' -> prudent, 'moyen' -> equilibre, 'je vise la "
            "performance' -> dynamique. "
            "En cas d'hésitation entre deux niveaux, choisir le plus prudent. "
            "null si la personne n'en parle pas."
        )
    )

    epargne_precaution_mois: float | None = Field(
        ge=0,
        description=(
            "Nombre de mois de dépenses courantes couverts par l'épargne "
            "disponible à côté (livrets, compte courant). "
            "Mettre 0 si la personne dit ne pas en avoir. "
            "Mettre null si elle n'aborde pas le sujet. "
            "La différence entre 0 et null est importante : 0 est une "
            "information, null est une absence d'information."
        )
    )

    resident_francais: bool | None = Field(
        description=(
            "true si la personne indique résider fiscalement en France. "
            "null si elle ne le précise pas. "
            "Ne jamais déduire ce champ du fait qu'elle écrit en français."
        )
    )

    # Observations SCF distinctes du risque déclaré et des mois de dépenses.
    # Le schéma API accepte null quand ces observations ne sont pas connues.
    age: float | None = Field(default=None, ge=18, le=120,
        description="Âge explicitement donné en années ; null si absent. Ne jamais inventer 40 ans.")
    part_actions_actuelle: float | None = Field(default=None, ge=0, le=1,
        description="Part ACTUELLE des actions directes et indirectes dans le patrimoine financier, ratio entre 0 et 1. Pas une part souhaitée ni la tolérance au risque. null si absente.")
    liquidites_mois_revenu: float | None = Field(default=None, ge=0,
        description="Liquidités en mois de REVENU habituel explicitement indiquées. Ne pas recopier les mois de DEPENSES de l'épargne de précaution. null si absent.")
    ratio_dette_actifs: float | None = Field(default=None, ge=0,
        description="Dette totale divisée par la valeur totale des actifs, ratio explicite (pas dette/revenu). 0 uniquement si aucune dette explicitement déclarée. null sinon.")


# Questions de collecte des cinq informations principales, associées aux champs du profil.
QUESTIONS = {
    "montant_eur": "Quel montant souhaitez-vous investir ?",
    "horizon_annees": "Dans combien d'années aurez-vous besoin de cet argent ?",
    "tolerance_risque": (
        "Si votre investissement perdait 20 % en quelques mois, que feriez-vous ?\n\n"
        "A. Je vendrais pour limiter mes pertes\n\n"
        "B. Je conserverais mon investissement en attendant une éventuelle remontée\n\n"
        "C. Je pourrais investir davantage pour profiter de la baisse"
    ),
    "epargne_precaution_mois": (
        "Avez-vous une épargne disponible à côté ? "
        "Combien de mois de dépenses couvre-t-elle environ ?"
    ),
    "resident_francais": "Résidez-vous fiscalement en France ?",
}
