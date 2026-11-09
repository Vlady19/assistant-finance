"""Calcule une analyse et une comparaison SCF depuis un profil JSON, sans appel LLM.
Exemple : python infer.py examples/profil_complet.json.
"""

import argparse
import json
from pathlib import Path
from app.models import Profil
from app.pipeline import calculer

def main():
    """Valide le fichier JSON fourni et affiche la trace des calculs locaux."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profil',type=Path)
    args=parser.parse_args()
    profil=Profil.model_validate_json(args.profil.read_text())
    print(json.dumps(calculer(profil),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
