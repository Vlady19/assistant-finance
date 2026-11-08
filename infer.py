"""Inférence hors interface : python infer.py profil.json.

Le JSON suit app.models.Profil ; voir examples/profil_complet.json.
Aucun appel au LLM : résultat structuré, reproductible et vérifiable.
"""
import argparse
import json
from pathlib import Path
from app.models import Profil
from app.pipeline import calculer

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profil',type=Path)
    args=parser.parse_args()
    profil=Profil.model_validate_json(args.profil.read_text())
    print(json.dumps(calculer(profil),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
