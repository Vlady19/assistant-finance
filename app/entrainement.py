"""Entraîne et évalue la segmentation K-Means sur le SCF 2022.
Sépare les familles train/test, compare les valeurs de K et sauvegarde le modèle et ses rapports.
"""

import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from .features import VARIABLES, BornerRatios

RACINE=Path(__file__).resolve().parents[1]
GRAINE=42


def preparer_donnees(brut):
    # Une famille n'apparaît qu'une fois : pas de fuite entre ses implicats.
    """Retient le premier implicat, exclut les ratios invalides et construit les variables.
    Renvoie les familles retenues, les quatre variables et le bilan des exclusions.
    """
    df=brut.loc[brut.y1.mod(10).eq(1)].copy()
    if df.yy1.duplicated().any():
        raise ValueError("Une famille apparaît plusieurs fois dans l'implicat retenu.")
    # Un ratio avec dénominateur nul est indéfini : remplacer zéro par un
    # inventerait une observation. On exclut ces familles et compte l'effet.
    valide=(df.fin.gt(0) & df.norminc.gt(0) & df.age.between(18,120)
            & df.equity.ge(0) & df.liq.ge(0) & df.levratio.ge(0))
    retenu=df.loc[valide].copy()
    X=pd.DataFrame({"age":retenu.age,"part_risquee":retenu.equity/retenu.fin,
                    "coussin_mois":12*retenu.liq/retenu.norminc,"levier":retenu.levratio})
    finies=np.isfinite(X).all(axis=1)
    return retenu.loc[finies], X.loc[finies], {"familles_initiales":len(df),"familles_retenues":int(finies.sum()),
             "familles_exclues":int(len(df)-finies.sum()),"fin_nul":int(df.fin.eq(0).sum()),"revenu_nul":int(df.norminc.eq(0).sum())}


def creer_pipeline(k=3, graine=GRAINE):
    """Assemble bornage, StandardScaler et K-Means avec une initialisation reproductible."""
    return Pipeline([("bornes",BornerRatios()),("scaler",StandardScaler()),
                     ("kmeans",KMeans(n_clusters=k,random_state=graine,n_init=10,max_iter=300))])


def silhouette(modele,X):
    """Mesure la séparation des groupes après les transformations du pipeline."""
    transforme=modele[:-1].transform(X)
    labels=modele.predict(X)
    return float(silhouette_score(transforme,labels,sample_size=min(2000,len(X)),random_state=GRAINE))


def entrainer():
    """Compare K, évalue le modèle retenu et sauvegarde le pipeline, le seuil et les rapports."""
    chemin=RACINE/'data/raw/scfp2022.parquet'
    brut=pd.read_parquet(chemin)
    familles,X,qualite=preparer_donnees(brut)
    # La sélection d'un implicat garantit une ligne par famille avant la séparation.
    train,test=train_test_split(X.index,test_size=.2,random_state=GRAINE)
    comparaisons=[]
    for k in (2,3,4):
        m=creer_pipeline(k).fit(X.loc[train])
        comparaisons.append({"k":k,"silhouette_train":silhouette(m,X.loc[train])})
    # K=3 est un choix de lisibilité ; les scores alternatifs sont conservés
    # dans le rapport, y compris lorsque K=4 obtient une meilleure silhouette.
    modele=creer_pipeline().fit(X.loc[train])
    labels_test=modele.predict(X.loc[test])
    stabilite=[]
    for graine in (7,21,84):
        autre=creer_pipeline(graine=graine).fit(X.loc[train])
        stabilite.append({"graine":graine,"ari_test":float(adjusted_rand_score(labels_test,autre.predict(X.loc[test])))})
    # Seuil heuristique : 99e percentile des distances minimales du train uniquement.
    seuil=float(np.quantile(modele.transform(X.loc[train]).min(axis=1),.99))
    labels_train=modele.predict(X.loc[train])
    # Revenir aux unités d'origine après bornage pour décrire les centres des groupes.
    centres=modele.named_steps['scaler'].inverse_transform(modele.named_steps['kmeans'].cluster_centers_)
    segments=[{"cluster":i,"effectif_train":int((labels_train==i).sum()),"moyennes_plafonnees":dict(zip(VARIABLES,map(float,c)))} for i,c in enumerate(centres)]
    part_sans_actions=familles.equity.eq(0).astype(float)
    rapport={"graine":GRAINE,"source_sha256":hashlib.sha256(chemin.read_bytes()).hexdigest(),"qualite":qualite,
        "effectif_train":len(train),"effectif_test":len(test),"familles_train":familles.loc[train,'yy1'].astype(int).tolist(),
        "familles_test":familles.loc[test,'yy1'].astype(int).tolist(),"comparaisons_train":comparaisons,
        "k_retenu":3,"justification_k":"Continuité avec l'EDA et lisibilité de trois segments. Choix de conception, pas optimum de silhouette revendiqué.",
        "silhouette_test":silhouette(modele,X.loc[test]),"stabilite_initialisations":stabilite,"distance_max":seuil,
        "taux_test_abstention_distance":float((modele.transform(X.loc[test]).min(axis=1)>seuil).mean()),
        "segments_train":segments,
        "sensibilite_ponderation_descriptive":{"sans_actions_non_pondere":float(part_sans_actions.mean()),
            "sans_actions_pondere":float(np.average(part_sans_actions,weights=familles.wgt))},
        "limites":["Un seul implicat ; incertitude d'imputation non estimée.",
                   "KMeans non pondéré ; sensibilité descriptive aux poids seulement, pas inférence d'enquête complète.",
                   "Population américaine, aucune validation externe française.",
                   "Liquidités / revenu et non mois de dépenses.",
                   "Distance de rejet : seuil heuristique, non probabilité de fiabilité."]}
    dest=RACINE/'models/segmentation.joblib'
    joblib.dump({"pipeline":modele,"distance_max":seuil,"source_sha256":rapport['source_sha256'],
                 "protocole":"SCF2022_implicat1_train80_test20_seed42"},dest)
    rapport['modele_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
    (RACINE/'reports/protocole_ml.json').write_text(json.dumps(rapport,ensure_ascii=False,indent=2))
    print(json.dumps({k:rapport[k] for k in ['qualite','effectif_train','effectif_test','comparaisons_train','silhouette_test','stabilite_initialisations']},ensure_ascii=False,indent=2))
    # Données test et attributions exportées pour une vérification hors chatbot.
    sorties=X.loc[test].copy();sorties.insert(0,'id_famille',familles.loc[test,'yy1'].astype(int))
    sorties['cluster']=labels_test
    sorties['distance']=modele.transform(X.loc[test]).min(axis=1)
    sorties['attribution_retenue']=sorties.distance.le(seuil)
    sorties.to_json(RACINE/'reports/predictions_test.json',orient='records',indent=2)

if __name__=='__main__':
    entrainer()
