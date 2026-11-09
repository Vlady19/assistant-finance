"""Applique les règles pédagogiques d'allocation sans appel LLM.
Calcule la capacité de risque, le niveau retenu, les répartitions et les alertes.
"""


from .models import Profil

# Seuils pédagogiques centralisés pour le calcul de capacité et les prérequis.

EPARGNE_PRECAUTION_MINIMALE_MOIS = 3.0
HORIZON_MINIMUM_ACTIONS_ANNEES = 5.0

NIVEAUX = {1: "prudent", 2: "equilibre", 3: "dynamique"}
NIVEAUX_INVERSE = {"prudent": 1, "equilibre": 2, "dynamique": 3}


def champs_manquants(profil: Profil) -> list[str]:
    """Liste les informations principales à None ; une valeur nulle reste connue."""
    return [
        champ for champ in ("montant_eur", "horizon_annees", "tolerance_risque", "epargne_precaution_mois", "resident_francais") if getattr(profil, champ) is None
    ]


def capacite_risque(profil: Profil) -> int | None:
    """Calcule un niveau de capacité de 1 à 3 selon l'horizon et la précaution.
    Renvoie None si l'horizon n'est pas connu.
    """
    if profil.horizon_annees is None:
        return None

    # L'horizon fixe la capacité initiale, avant le contrôle de la précaution.
    if profil.horizon_annees < 2:
        niveau = 1
    elif profil.horizon_annees < HORIZON_MINIMUM_ACTIONS_ANNEES:
        niveau = 2
    else:
        niveau = 3

    # Une précaution insuffisante ramène la capacité au niveau prudent.
    manque_de_coussin = (
        profil.epargne_precaution_mois is not None
        and profil.epargne_precaution_mois < EPARGNE_PRECAUTION_MINIMALE_MOIS
    )
    if manque_de_coussin:
        niveau = 1

    return niveau


def niveau_retenu(profil: Profil) -> int | None:
    """Retient le minimum entre capacité calculée et tolérance déclarée."""
    capacite = capacite_risque(profil)
    if capacite is None or profil.tolerance_risque is None:
        return None

    declare = NIVEAUX_INVERSE[profil.tolerance_risque]
    return min(capacite, declare)


def ecart_avec_le_souhait(profil: Profil) -> int | None:
    """Mesure l'écart entre tolérance et capacité ; positif si la tolérance dépasse la capacité."""
    capacite = capacite_risque(profil)
    if capacite is None or profil.tolerance_risque is None:
        return None
    return NIVEAUX_INVERSE[profil.tolerance_risque] - capacite


# Répartitions pédagogiques fixes ; elles ne sont pas optimisées ni apprises sur le SCF.
REPARTITIONS = {
    1: {"Fonds sécurisés (fonds euros, monétaire)": 75, "Actions diversifiées": 25},
    2: {"Fonds sécurisés (fonds euros, monétaire)": 45, "Actions diversifiées": 55},
    3: {"Fonds sécurisés (fonds euros, monétaire)": 20, "Actions diversifiées": 80},
}


def repartition(niveau: int) -> dict[str, int]:
    """Renvoie la répartition pédagogique fixe associée au niveau retenu."""
    return REPARTITIONS[niveau]


def alertes(profil: Profil) -> list[str]:
    """Construit les avertissements liés à l'horizon, la précaution, le risque et la résidence."""
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
    """Vérifie le profil complet, l'horizon minimal et la précaution minimale.
    Ces seuils sont des règles pédagogiques, pas des résultats appris sur le SCF.
    """
    return (not champs_manquants(profil)
            and profil.horizon_annees >= 2
            and profil.epargne_precaution_mois >= EPARGNE_PRECAUTION_MINIMALE_MOIS)
