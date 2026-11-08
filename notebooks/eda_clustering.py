"""EDA mise à jour depuis celle de Claude. Exécution : python -m notebooks.eda_clustering.

Ce script fait l'EDA ; python -m app.entrainement valide et sauvegarde le ML.
Séparer ces deux tâches évite qu'un graphique réentraîne le modèle de l'app.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from app.entrainement import preparer_donnees

RACINE=Path(__file__).resolve().parents[1]

def main():
    brut=pd.read_parquet(RACINE/'data/raw/scfp2022.parquet')
    df,X,qualite=preparer_donnees(brut)
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    axes[0,0].hist(X.age,bins=16,color='#366b9d');axes[0,0].set_title('Âge des personnes de référence');axes[0,0].set_xlabel('Années')
    axes[0,1].hist(100*X.part_risquee.clip(0,1),bins=20,color='#548b70');axes[0,1].set_title('Actions / patrimoine financier');axes[0,1].set_xlabel('Part en %')
    axes[1,0].hist(X.coussin_mois.clip(0,24),bins=24,color='#ae7744');axes[1,0].set_title('Liquidités / revenu mensuel habituel');axes[1,0].set_xlabel('Mois de REVENU (plafond 24)')
    axes[1,1].hist(100*X.levier.clip(0,1),bins=20,color='#806599');axes[1,1].set_title('Dette / actifs totaux');axes[1,1].set_xlabel('Ratio en % (plafond 100)')
    for ax in axes.flat: ax.set_ylabel('Nombre de ménages')
    fig.suptitle('SCF 2022 — premier implicat, observations valides, non pondéré')
    fig.tight_layout();fig.savefig(RACINE/'reports/figures/eda_exploration.png',dpi=160);plt.close(fig)
    protocole=json.loads((RACINE/'reports/protocole_ml.json').read_text())
    fig,ax=plt.subplots(figsize=(7,4))
    valeurs=protocole['comparaisons_train']; ax.bar([r['k'] for r in valeurs],[r['silhouette_train'] for r in valeurs])
    ax.set_xticks([2,3,4]);ax.set_xlabel('Nombre de groupes');ax.set_ylabel('Silhouette sur train')
    ax.set_title('KMeans : k=3 conservé pour la lisibilité, k=4 mieux séparé')
    fig.tight_layout();fig.savefig(RACINE/'reports/figures/silhouette_scores.png',dpi=160);plt.close(fig)
    dictionnaire={
        'age':"Âge de la personne de référence, années.",
        'part_risquee':"equity / fin : actions directes et indirectes / patrimoine financier ; pas une tolérance déclarée.",
        'coussin_mois':"12 × liq / norminc : liquidités / revenu mensuel habituel ; pas des mois de dépenses.",
        'levier':"levratio : dettes / actifs totaux.",
        'y1':"Identifie l'implicat ; premier retenu via y1 modulo 10 = 1 ; jamais une feature.",
        'yy1':"Identifiant famille, utilisé pour contrôler la séparation train/test ; jamais une feature.",
        'wgt':"Poids d'enquête, utilisé pour une comparaison descriptive de sensibilité, pas pour entraîner KMeans.",
        'educ':"Non utilisé dans le ML. La modalité -1 signifie moins d'une première année de scolarité, pas une valeur manquante."}
    rapport={'source':'https://www.federalreserve.gov/econres/scfindex.htm','qualite':qualite,
             'dictionnaire':dictionnaire,'variables_modele':list(X.columns),
             'limites':protocole['limites'],'correlations':X.corr().to_dict()}
    (RACINE/'reports/eda.json').write_text(json.dumps(rapport,ensure_ascii=False,indent=2))
    print('EDA et deux figures mises à jour.')

if __name__=='__main__':main()
