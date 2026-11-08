"""
app/regles.py — le cerveau du projet. Aucun modèle de langage ici.

# 🧮 Fait les calculs et applique les règles métier

=============================================================================
 POURQUOI CE FICHIER EXISTE
=============================================================================

Ouvre-le et cherche le mot « client », « prompt » ou « openai ». Il n'y en a
aucun. C'est délibéré, et c'est toute la leçon de la V2.

Compare deux façons de faire :

  A) Tu écris dans le system prompt : « si l'horizon est inférieur à 5 ans,
     recommande une allocation prudente ». Le modèle suivra... la plupart du
     temps. Tu ne sauras jamais quand il ne l'a pas fait.

  B) Tu écris `if horizon < 5:` dans une fonction Python. Ça marche à 100 %,
     tu peux le tester, et n'importe qui peut lire la règle et la contester.

Un LLM est excellent pour comprendre « j'ai dix mille balles de côté » et en
tirer 10000. Il est inutile pour calculer 10000 × 0,3. Confie-lui la
compréhension du langage, garde le raisonnement chiffré pour toi.

Effet secondaire immédiat : ces fonctions sont testables. Tu peux appeler
`capacite_risque(...)` cent fois avec cent profils différents, sans dépenser
un centime d'API et sans attendre le réseau. C'est impossible avec du code
noyé dans un prompt.
"""

from .models import Profil

# ─────────────────────────────────────────────────────────────────────────
# Les seuils sont des constantes nommées, pas des nombres perdus dans le
# code. Quand tu voudras discuter « pourquoi 3 mois et pas 6 ? », tu sauras
# où regarder — et tu n'auras qu'un seul endroit à modifier.
# ─────────────────────────────────────────────────────────────────────────

EPARGNE_PRECAUTION_MINIMALE_MOIS = 3.0
HORIZON_MINIMUM_ACTIONS_ANNEES = 5.0

NIVEAUX = {1: "prudent", 2: "equilibre", 3: "dynamique"}
NIVEAUX_INVERSE = {"prudent": 1, "equilibre": 2, "dynamique": 3}


def champs_manquants(profil: Profil) -> list[str]:
    """Renvoie la liste des champs restés à None.

    `model_dump()` transforme l'objet Pydantic en dictionnaire Python
    classique. On parcourt ce dictionnaire et on garde les clés dont la
    valeur est None.

    Attention à la nuance : on teste `is None` et non `not valeur`. Avec
    `not valeur`, le chiffre 0 serait considéré comme manquant — or 0 mois
    d'épargne de précaution est une information capitale, pas un vide.
    """
    return [
        champ for champ in ("montant_eur", "horizon_annees", "tolerance_risque", "epargne_precaution_mois", "resident_francais") if getattr(profil, champ) is None
    ]


def capacite_risque(profil: Profil) -> int | None:
    """Calcule le risque que la situation de la personne *permet* (1 à 3).

    À distinguer de la tolérance déclarée, qui est ce qu'elle *dit* accepter.
    Quelqu'un peut se sentir audacieux tout en ayant besoin de son argent
    dans dix-huit mois : son ressenti ne change rien à cette contrainte.

    Renvoie None si l'horizon est inconnu. Sans horizon, la question n'a
    pas de sens, et il vaut mieux poser la question qu'inventer une réponse.
    """
    if profil.horizon_annees is None:
        return None

    # L'horizon domine tout le reste : c'est la seule variable qui détermine
    # si on a le temps d'encaisser une baisse avant d'avoir besoin des fonds.
    if profil.horizon_annees < 2:
        niveau = 1
    elif profil.horizon_annees < HORIZON_MINIMUM_ACTIONS_ANNEES:
        niveau = 2
    else:
        niveau = 3

    # Sans coussin de sécurité, le moindre imprévu force à vendre — et les
    # imprévus tombent rarement quand les marchés sont au plus haut.
    manque_de_coussin = (
        profil.epargne_precaution_mois is not None
        and profil.epargne_precaution_mois < EPARGNE_PRECAUTION_MINIMALE_MOIS
    )
    if manque_de_coussin:
        niveau = 1

    return niveau


def niveau_retenu(profil: Profil) -> int | None:
    """Le niveau effectivement appliqué : le plus faible des deux.

    Règle simple et défendable :
      - la capacité ne doit jamais pousser quelqu'un au-delà de ce qu'il
        accepte psychologiquement (il vendrait à la première secousse)
      - la tolérance ne doit jamais dépasser ce que sa situation permet
        (il serait forcé de vendre au mauvais moment)

    Donc : minimum des deux. Une ligne de code, mais c'est le cœur du
    raisonnement de tout conseiller sérieux.
    """
    capacite = capacite_risque(profil)
    if capacite is None or profil.tolerance_risque is None:
        return None

    declare = NIVEAUX_INVERSE[profil.tolerance_risque]
    return min(capacite, declare)


def ecart_avec_le_souhait(profil: Profil) -> int | None:
    """Positif si la personne voulait plus de risque que sa situation permet.

    C'est le chiffre le plus utile à lui montrer : il transforme un refus
    en explication.
    """
    capacite = capacite_risque(profil)
    if capacite is None or profil.tolerance_risque is None:
        return None
    return NIVEAUX_INVERSE[profil.tolerance_risque] - capacite


# Trois répartitions volontairement grossières. Elles servent à illustrer le
# mécanisme, pas à être suivies. La V4 les remplacera par quelque chose de
# sérieux, avec les enveloppes fiscales françaises et de vraies classes
# d'actifs.
REPARTITIONS = {
    1: {"Fonds sécurisés (fonds euros, monétaire)": 75, "Actions diversifiées": 25},
    2: {"Fonds sécurisés (fonds euros, monétaire)": 45, "Actions diversifiées": 55},
    3: {"Fonds sécurisés (fonds euros, monétaire)": 20, "Actions diversifiées": 80},
}


def repartition(niveau: int) -> dict[str, int]:
    return REPARTITIONS[niveau]


def alertes(profil: Profil) -> list[str]:
    """Points de vigilance calculés depuis le profil.

    Ce ne sont pas des avertissements décoratifs : ce sont des prérequis.
    Investir sans épargne de précaution, ce n'est pas « un peu risqué »,
    c'est faire les choses dans le mauvais ordre.
    """
    messages = []

    if (
        profil.epargne_precaution_mois is not None
        and profil.epargne_precaution_mois < EPARGNE_PRECAUTION_MINIMALE_MOIS
    ):
        messages.append(
            "Avant d'investir, l'usage est de sécuriser 3 à 6 mois de dépenses "
            "sur des livrets disponibles. Sans ce coussin, une baisse de marché "
            "vous forcerait à vendre au pire moment."
        )

    if profil.horizon_annees is not None and profil.horizon_annees < 2:
        messages.append(
            "Sur moins de deux ans, une exposition aux actions relève du pari "
            "plus que de l'investissement."
        )

    ecart = ecart_avec_le_souhait(profil)
    if ecart is not None and ecart > 0:
        messages.append(
            "Le niveau de risque souhaité dépasse ce que votre horizon et "
            "votre épargne de précaution permettent. La répartition proposée "
            "retient le niveau le plus prudent des deux."
        )

    if profil.resident_francais is False:
        messages.append(
            "Cet outil ne traite que la fiscalité française. Hors de France, "
            "les règles applicables sont différentes."
        )

    return messages


def allocation_autorisee(profil: Profil) -> bool:
    """Seuils pédagogiques du projet, pas seuils optimaux démontrés par SCF."""
    return (not champs_manquants(profil)
            and profil.horizon_annees >= 2
            and profil.epargne_precaution_mois >= EPARGNE_PRECAUTION_MINIMALE_MOIS)
