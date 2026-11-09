"""Extrait un Profil structuré depuis un message avec l'API OpenAI.
Utilise le profil connu et la dernière question pour interpréter les réponses courtes.
"""


from .config import MODELE, obtenir_client, ServiceIndisponible
from .models import Profil

# Consigne d'extraction envoyée au LLM ; format() ajoute le contexte du profil.
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
    """Extrait les informations du message selon le schéma Profil.
    Le résumé du profil et la dernière question apportent le contexte ;
    la fusion des valeurs est effectuée ensuite par conversation.py.
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