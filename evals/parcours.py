"""Parcours réels avec références définies indépendamment de la réponse de l'agent.

Les textes sont synthétiques. Les assertions testent les résultats structurés,
pas une formulation exacte. Lancer : python -m evals.parcours (clé API nécessaire).
"""
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app import conversation, pipeline, llm, intents
from app.config import MODELE

EXTRACTIONS=[
    ("Je veux investir 12000 euros sur 10 ans, prudent, résident fiscal français, avec 6 mois de dépenses en réserve.",
     {"montant_eur":12000.,"horizon_annees":10.,"tolerance_risque":"prudent","epargne_precaution_mois":6.,"resident_francais":True,
      "age":None,"part_actions_actuelle":None,"liquidites_mois_revenu":None,"ratio_dette_actifs":None}),
    ("J'ai 62 ans. Mes actions représentent actuellement 43 % de mon patrimoine financier. Mes liquidités représentent 2,7 mois de revenu habituel. Mes dettes valent 9 % de mes actifs. Je suis prudent.",
     {"age":62.,"part_actions_actuelle":.43,"liquidites_mois_revenu":2.7,"ratio_dette_actifs":.09,"epargne_precaution_mois":None,"tolerance_risque":"prudent"}),
    ("Je suis dynamique, je dispose de 6 mois de dépenses d'avance.",
     {"age":None,"ratio_dette_actifs":None,"part_actions_actuelle":None,"liquidites_mois_revenu":None,"epargne_precaution_mois":6.}),
    ("J'aimerais placer de l'argent à long terme.", {"montant_eur":None,"horizon_annees":None,"resident_francais":None}),
    ("Je peux épargner 300 euros chaque mois.", {"montant_eur":None}),
]


def lancer():
    lignes=[]
    for question,attendu in EXTRACTIONS:
        try:
            obtenu=llm.extraire_profil('Scénario entièrement fictif pour un test logiciel : '+question,'aucun').model_dump()
            ok=all(obtenu[k]==v for k,v in attendu.items())
            lignes.append(dict(type='extraction',question=question,attendu=attendu,obtenu=obtenu,reussi=ok))
        except Exception as e:
            lignes.append(dict(type='extraction',question=question,reussi=False,erreur=type(e).__name__))
    cas=[
        ("Je veux placer 10000 euros sur 15 ans, prudent, résident fiscal français, 6 mois de dépenses en réserve. J'ai 62 ans, 43 % de mon patrimoine financier actuellement en actions, des liquidités couvrant 2,7 mois de revenu habituel et un ratio dettes sur actifs de 9 %.", 'allocation',True,'utilise'),
        ("J'ai 10000 euros à investir, sur un an, dynamique, résident fiscal français, sans épargne de précaution.", 'allocation',True,'informations_manquantes'),
        ("Le S&P 500 ou le MSCI World pour mon PEA ?",'actif_precis',False,None),
        ("Explique le principe de diversification.",'pedagogie',False,None),
        ("Donne le cours actuel de Microsoft.",'donnees_marche',False,None),
        ("Je veux écrire un bail commercial.",'hors_sujet',False,None),
    ]
    def parcours(cas):
        question,intent,termine,ml=cas
        try:
            debut=time.perf_counter();r=pipeline.traiter('Scénario entièrement fictif pour un test logiciel : '+question,conversation.profil_vide())
            obtenu={'intent':r.intent.value,'termine':r.termine,'texte':r.texte,'dossier':r.dossier,'trace':r.trace,'repli':r.repli_utilise,
                    'validation':r.problemes_validation,'duree_s':round(time.perf_counter()-debut,2)}
            ok=r.intent.value==intent and r.termine==termine
            if ml: ok=ok and r.trace.get('clustering',{}).get('statut')==ml
            if 'sur un an' in question: ok=ok and r.trace.get('allocation_suspendue') is True
            if ml=='utilise': ok=ok and [v['montant_eur'] for v in r.trace['allocation_illustrative']]==[7500.,2500.]
            return dict(type='parcours',question=question,attendu={'intent':intent,'termine':termine,'clustering':ml},obtenu=obtenu,reussi=ok)
        except Exception as e:
            return dict(type='parcours',question=question,reussi=False,erreur=type(e).__name__)
    with ThreadPoolExecutor(max_workers=3) as pool:
        lignes.extend(pool.map(parcours,cas))
    # Dialogue complet : vérifier que les corrections et une interruption
    # pédagogique ne détruisent pas les informations déjà recueillies.
    profil=conversation.profil_vide();derniere=None;dialogue=[]
    for message in ["Je veux placer 10000 euros.","J'ai 6 mois de dépenses d'avance.","Que signifie diversifier ?","Sur 15 ans.","A","Oui"]:
        r=pipeline.traiter(('Scénario entièrement fictif pour un test logiciel : ' if not dialogue else '')+message,profil,derniere)
        profil,derniere=r.profil,r.derniere_question
        dialogue.append({'message':message,'texte':r.texte,'intent':r.intent.value,'profil':profil.model_dump(),'termine':r.termine})
    lignes.append({'type':'dialogue','obtenu':dialogue,'attendu':{'montant_eur':10000,'horizon_annees':15,'tolerance_risque':'prudent','resident_francais':True},
                   'reussi':r.termine and profil.montant_eur==10000 and profil.horizon_annees==15 and profil.tolerance_risque=='prudent' and profil.resident_francais is True})
    rapport={'modele':MODELE,'total':len(lignes),'reussis':sum(x['reussi'] for x in lignes),'cas':lignes}
    (Path(__file__).resolve().parents[1]/'reports/evaluation_parcours.json').write_text(json.dumps(rapport,ensure_ascii=False,indent=2))
    print('Parcours/extractions réels :',rapport['reussis'],'/',rapport['total'])
    return rapport['reussis']==rapport['total']

if __name__=='__main__':
    raise SystemExit(0 if lancer() else 1)
