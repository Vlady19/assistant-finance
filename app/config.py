"""Charge la configuration OpenAI depuis l'environnement ou le fichier .env.
Crée le client à la demande pour permettre les calculs locaux sans clé API.
"""

import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI

RACINE = Path(__file__).resolve().parents[1]
load_dotenv(RACINE / ".env", override=False)
MODELE = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

class ServiceIndisponible(RuntimeError):
    """Erreur présentable à l'utilisateur, sans clé ni réponse brute du fournisseur."""

@lru_cache(maxsize=1)
def obtenir_client():
    """Crée et met en cache le client ; signale l'absence de clé au premier besoin d'API."""
    cle = os.getenv("OPENAI_API_KEY")
    if not cle:
        raise ServiceIndisponible("Clé API absente : renseignez OPENAI_API_KEY dans .env.")
    return OpenAI(api_key=cle, timeout=30.0, max_retries=1)
