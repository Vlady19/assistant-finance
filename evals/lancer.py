"""Évaluation API réelle, résultats persistés. Lancer : python -m evals.lancer."""
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from app.intents import classer, PROMPT_CLASSIFICATION
from app.config import MODELE
from evals.cas import CAS
from evals.cas_generalisation import CAS as NOUVEAUX


def lancer():
    def evaluer(item):
        jeu, (question, attendu, note) = item
        debut=time.perf_counter()
        try:
            r=classer(question)
            obtenu=r.intent.value
            justification=r.justification
        except Exception as erreur:
            obtenu="ERREUR:" + type(erreur).__name__
            justification="Appel échoué ; aucun détail sensible enregistré."
        resultat={"jeu":jeu,"question":question,"attendu":attendu.value,"obtenu":obtenu,
                  "reussi":obtenu==attendu.value,"note":note,"justification":justification,
                  "duree_s":round(time.perf_counter()-debut,3)}
        print(f"{jeu}: {obtenu} — attendu {attendu.value}",flush=True)
        return resultat
    with ThreadPoolExecutor(max_workers=3) as pool:
        lignes=list(pool.map(evaluer,[("historique",c) for c in CAS]+[("generalisation",c) for c in NOUVEAUX]))
    rapport={"date_utc":datetime.now(timezone.utc).isoformat(),"modele":MODELE,
             "temperature":"paramètre omis ; configuration historique conservée, non-déterminisme possible",
             "prompt_sha256":hashlib.sha256(PROMPT_CLASSIFICATION.encode()).hexdigest(),
             "questions_litterales_dans_prompt":sum(q in PROMPT_CLASSIFICATION for q,_,_ in CAS+NOUVEAUX),
             "resultats":lignes,"scores":{}}
    for jeu in ["historique","generalisation"]:
        subset=[l for l in lignes if l['jeu']==jeu]
        rapport['scores'][jeu]={"reussis":sum(l['reussi'] for l in subset),"total":len(subset)}
    sortie=Path(__file__).resolve().parents[1]/'reports/evaluation_classification.json'
    sortie.parent.mkdir(parents=True,exist_ok=True)
    sortie.write_text(json.dumps(rapport,ensure_ascii=False,indent=2))
    print(rapport['scores'],flush=True)
    return sum(not l['reussi'] for l in lignes)

if __name__=='__main__':
    raise SystemExit(1 if lancer() else 0)
