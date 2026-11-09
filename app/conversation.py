"""Gère la mémoire structurée du profil entre les messages.
Fusionne les nouvelles valeurs et détermine la prochaine information à demander.
"""


from .models import Profil


def profil_vide() -> Profil:
    """Crée un profil entièrement inconnu, avec None dans tous les champs.
    Les champs requis par le schéma sont fournis explicitement.
    """
    return Profil(**{champ: None for champ in Profil.model_fields})


def fusionner(ancien: Profil, nouveau: Profil) -> Profil:
    """Met à jour le profil avec les nouvelles valeurs non nulles.
    Conserve les valeurs connues si le message ne les renseigne pas, y compris les zéros.
    """
    donnees = ancien.model_dump()

    # Mettre à jour uniquement les valeurs connues, y compris zéro.
    for champ, valeur in nouveau.model_dump().items():
        if valeur is not None:
            donnees[champ] = valeur

    # La reconstruction valide de nouveau les données après leur fusion.
    return Profil(**donnees)


# Ordre de collecte : vérifier la précaution avant de compléter les autres informations.
ORDRE_DES_QUESTIONS = [
    "epargne_precaution_mois",
    "horizon_annees",
    "montant_eur",
    "tolerance_risque",
    "resident_francais",
]


def prochain_champ_manquant(profil: Profil) -> str | None:
    """Renvoie le premier champ principal absent, selon l'ordre de collecte, ou None."""
    donnees = profil.model_dump()

    for champ in ORDRE_DES_QUESTIONS:
        if donnees[champ] is None:
            return champ

    return None


def est_complet(profil: Profil) -> bool:
    """Indique si les cinq informations principales du profil sont connues."""
    return prochain_champ_manquant(profil) is None


def resume_lisible(profil: Profil) -> str:
    """Résume les valeurs connues pour fournir le contexte au modèle d'extraction."""
    lignes = []
    for champ, valeur in profil.model_dump().items():
        if valeur is not None:
            lignes.append(f"- {champ} : {valeur}")

    return "\n".join(lignes) if lignes else "(rien de connu pour l'instant)"
