"""
app/models.py — le formulaire que le modèle doit remplir.

# Sert à décrire la structure des données que l'on souhaite extraire du message de l'utilisateur, 
# et à valider la réponse du modèle.

=============================================================================
 LE CONCEPT NOUVEAU DE LA V2 : LA SORTIE STRUCTURÉE
=============================================================================

En V1, tu recevais du texte. Du texte, un programme ne peut rien en faire :
impossible de calculer avec, de le stocker en base, de le tester.

Ici, on inverse. On décrit à l'avance la forme exacte de ce qu'on veut, et
le modèle est *contraint* de la respecter. Pas « il essaie de respecter » :
contraint, techniquement, au moment de la génération.

Une classe Pydantic sert à deux choses en même temps :
  1. elle est traduite en JSON Schema et envoyée au modèle comme gabarit
  2. elle valide et convertit la réponse reçue en objet Python utilisable

C'est le même objet qui fait le contrat et la vérification. C'est pour ça
que Pydantic est partout dans les projets d'IA générative.
"""

from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class Profil(BaseModel):
    """Contrat commun au chat, au formulaire et à l'inférence.

    Les cinq champs historiques sont requis mais peuvent valoir None.
    Les quatre observations SCF sont facultatives lors d'un appel Python,
    pour préserver les profils V5. Le SDK convertit ce modèle en schéma
    strict pour l'API : même ces champs sont alors présents, quitte à être null.
    La sortie structurée garantit un format, pas la véracité de l'extraction.
    Pydantic vérifie ensuite bornes, finitude et valeurs autorisées.
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

    # V6 : observations facultatives pour comparer aux ménages SCF.
    # Elles ne sont PAS déduites de la tolérance, ni des mois de dépenses.
    # Le SDK rend ces propriétés requises/nullables dans le schéma envoyé.
    age: float | None = Field(default=None, ge=18, le=120,
        description="Âge explicitement donné en années ; null si absent. Ne jamais inventer 40 ans.")
    part_actions_actuelle: float | None = Field(default=None, ge=0, le=1,
        description="Part ACTUELLE des actions directes et indirectes dans le patrimoine financier, ratio entre 0 et 1. Pas une part souhaitée ni la tolérance au risque. null si absente.")
    liquidites_mois_revenu: float | None = Field(default=None, ge=0,
        description="Liquidités en mois de REVENU habituel explicitement indiquées. Ne pas recopier les mois de DEPENSES de l'épargne de précaution. null si absent.")
    ratio_dette_actifs: float | None = Field(default=None, ge=0,
        description="Dette totale divisée par la valeur totale des actifs, ratio explicite (pas dette/revenu). 0 uniquement si aucune dette explicitement déclarée. null sinon.")


# Le nom lisible de chaque champ, pour l'affichage. On garde ça ici, à côté
# du schéma, pour ne pas avoir à chercher ailleurs quand on ajoute un champ.
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
