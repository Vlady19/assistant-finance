"""
app/conversation.py — la mémoire de l'application.

# Gère le profil, la fusion et les champs manquants
=============================================================================
 LA NOTION NOUVELLE DE LA V3 : L'ÉTAT
=============================================================================

En V2, chaque message repartait de zéro. Si la personne écrivait « 10000 € »
puis « sur 10 ans », le second message effaçait le premier : le profil ne
contenait plus que l'horizon.

Il faut donc conserver ce qu'on a déjà appris, et le compléter à chaque tour.

UNE IDÉE IMPORTANTE
  Beaucoup de tutoriels stockent l'historique complet des messages et le
  renvoient en entier au modèle à chaque appel. Ça fonctionne, mais ça coûte
  de plus en plus cher, ça devient lent, et le modèle finit par se perdre
  dans un long fil.

  Ici, la mémoire est le `Profil` lui-même. Cinq champs de base et quatre observations facultatives. Quelle que soit la
  longueur de la conversation, l'état reste de taille constante, il est
  lisible d'un coup d'œil, et tu peux l'enregistrer en base de données.

  Retiens la formulation : on ne mémorise pas la conversation, on mémorise
  ce qu'on en a appris.

Ce fichier ne contient aucun appel au modèle. Comme `regles.py`, c'est du
Python pur, donc testable.
"""

from .models import Profil


def profil_vide() -> Profil:
    """Crée un profil dont tous les champs valent None.

    Pourquoi cette fonction plutôt qu'un simple `Profil()` ?

    Souviens-toi de la V2 : on a délibérément écrit `float | None` SANS
    valeur par défaut, pour satisfaire le mode strict d'OpenAI. Conséquence
    directe : Pydantic exige qu'on fournisse chaque champ à la construction.

    C'est le prix de ce choix, et il se paie une seule fois, ici.
    """
    return Profil(**{champ: None for champ in Profil.model_fields})


def fusionner(ancien: Profil, nouveau: Profil) -> Profil:
    """Combine le profil connu et ce qui vient d'être extrait.

    LA RÈGLE, EN UNE PHRASE :
        le nouveau tour enrichit et corrige, mais il n'efface jamais.

    Concrètement :
      - le nouveau message dit quelque chose  -> on prend la nouvelle valeur
        (la personne apporte une info, ou se corrige : « en fait 15000 »)
      - le nouveau message ne dit rien (None) -> on garde l'ancienne valeur

    Sans cette seconde ligne, chaque message détruirait le contexte accumulé.
    C'est cinq lignes de code, mais c'est tout le sujet de cette version.
    """
    donnees = ancien.model_dump()

    for champ, valeur in nouveau.model_dump().items():
        if valeur is not None:
            donnees[champ] = valeur

    # On reconstruit un objet Pydantic : les données repassent par la
    # validation. Si quelque chose ne colle pas, on le sait tout de suite.
    return Profil(**donnees)


# L'ordre dans lequel on réclame les informations manquantes.
#
# Ce n'est pas arbitraire. L'épargne de précaution vient en premier parce
# que c'est un prérequis : si la personne n'en a pas, la conversation sur
# l'allocation n'a pas lieu d'être, et autant le découvrir tout de suite
# plutôt qu'après trois questions.
ORDRE_DES_QUESTIONS = [
    "epargne_precaution_mois",
    "horizon_annees",
    "montant_eur",
    "tolerance_risque",
    "resident_francais",
]


def prochain_champ_manquant(profil: Profil) -> str | None:
    """Renvoie le nom du prochain champ à demander, ou None si complet.

    On renvoie UN seul champ, pas la liste entière.

    En V2 on affichait les quatre questions d'un coup. C'est efficace pour
    un programme, désagréable pour un humain : ça ressemble à un formulaire
    administratif et le taux d'abandon grimpe. Une question à la fois, c'est
    une conversation.
    """
    donnees = profil.model_dump()

    for champ in ORDRE_DES_QUESTIONS:
        if donnees[champ] is None:
            return champ

    return None


def est_complet(profil: Profil) -> bool:
    return prochain_champ_manquant(profil) is None


def resume_lisible(profil: Profil) -> str:
    """Le profil en texte court, pour l'injecter dans le prompt d'extraction.

    On envoie au modèle ce qu'on sait déjà, pour deux raisons :
      1. il comprend « oui » ou « 10 ans » comme la réponse à une question
      2. il ne repart pas de zéro et ne contredit pas l'existant sans raison
    """
    lignes = []
    for champ, valeur in profil.model_dump().items():
        if valeur is not None:
            lignes.append(f"- {champ} : {valeur}")

    return "\n".join(lignes) if lignes else "(rien de connu pour l'instant)"
