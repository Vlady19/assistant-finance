"""
app/llm.py — V3

# 🤖 Extrait les informations du message vers le Profil

Une seule différence avec la V2 : la fonction reçoit maintenant le profil
déjà connu et la dernière question posée, et les transmet au modèle.

Pourquoi c'est nécessaire ? Imagine la conversation :

    Assistant : Résidez-vous fiscalement en France ?
    Vous       : oui

Le mot « oui », isolé, ne veut rien dire. Le modèle a besoin de savoir à
quelle question il répond. On lui donne donc juste ce qu'il faut de
contexte — pas tout l'historique, seulement l'utile.
"""

from .config import MODELE, obtenir_client, ServiceIndisponible
from .models import Profil

# Remarque les accolades {profil_connu} et {derniere_question} : ce sont des
# emplacements que la méthode .format() remplira juste avant l'envoi.
PROMPT_EXTRACTION = """\
Tu extrais des informations d'un message. Tu ne réponds pas à la question posée,
tu ne donnes aucun conseil.

Règle absolue : n'extrais que ce qui est écrit. Si une information n'est pas
dans le message, mets null.

Ne déduis jamais un champ à partir d'un autre. Ne déduis pas la résidence
fiscale de la langue employée. Ne déduis pas la tolérance au risque du montant
investi. Une valeur inventée est bien plus grave qu'une valeur manquante : un
champ null déclenche une question, un champ inventé produit une recommandation
fausse que personne ne remarquera.

CE QUE L'ON SAIT DÉJÀ DE CETTE PERSONNE
{profil_connu}

Ne répète PAS ces valeurs dans ta réponse, sauf si le message actuel les
confirme ou les corrige. Pour tout ce dont le message ne parle pas, mets null :
la fusion avec l'existant est faite par le code, pas par toi.

DERNIÈRE QUESTION POSÉE À LA PERSONNE
{derniere_question}

Le message que tu reçois est probablement la réponse à cette question.
Interprète-le dans ce sens : « oui » à une question sur la résidence fiscale
signifie resident_francais = true ; « 10 ans » à une question sur l'horizon
signifie horizon_annees = 10 ; « aucune » à une question sur l'épargne de
précaution signifie epargne_precaution_mois = 0.
"""


def extraire_profil(
    message: str,
    profil_connu_resume: str,
    derniere_question: str | None = None,
) -> Profil:
    """Extrait un profil du message, en tenant compte du contexte connu.

    `profil_connu_resume` est le texte produit par
    conversation.resume_lisible(). On passe du texte déjà formaté plutôt
    qu'un objet Profil : ce fichier n'a pas à savoir comment on met en forme
    un profil, c'est le rôle de conversation.py. Chaque fichier son métier.
    """

    systeme = PROMPT_EXTRACTION.format(
        profil_connu=profil_connu_resume,
        derniere_question=derniere_question or "(aucune, c'est le premier message)",
    )

    reponse = obtenir_client().chat.completions.parse(
        model=MODELE,
        messages=[
            {"role": "system", "content": systeme},
            {"role": "user", "content": message},
        ],
        response_format=Profil,
    )

    profil = reponse.choices[0].message.parsed

    if profil is None:
        raise ServiceIndisponible(
            "Le modèle n'a pas renvoyé de profil exploitable. "
            "Cela arrive s'il refuse de répondre ou si la réponse est tronquée."
        )

    return profil