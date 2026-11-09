"""Prépare le SCF 2022 depuis le ZIP officiel ou son cache local.
Vérifie les colonnes, exporte le Parquet et enregistre l'empreinte de la source.
"""

from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hashlib
import json
import urllib.request
import pandas as pd

RACINE=Path(__file__).resolve().parents[1]
URL='https://www.federalreserve.gov/econres/files/scfp2022s.zip'

def main():
    """Convertit l'archive SCF en Parquet et enregistre la provenance des données."""
    dossier=RACINE/'data/raw';dossier.mkdir(parents=True,exist_ok=True)
    archive=dossier/'scfp2022s.zip'
    if not archive.exists():
        requete=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(requete,timeout=60) as reponse:
                archive.write_bytes(reponse.read())
        except OSError as erreur:
            raise SystemExit('Téléchargement SCF indisponible. Télécharger le ZIP depuis la source officielle et le placer dans data/raw/scfp2022s.zip.') from erreur
    with ZipFile(archive) as z:
        fichiers=[n for n in z.namelist() if n.endswith('.dta')]
        if len(fichiers)!=1: raise ValueError('Contenu ZIP inattendu.')
        # Conserver les codes numériques Stata pour respecter les définitions des variables.
        df=pd.read_stata(BytesIO(z.read(fichiers[0])),convert_categoricals=False)
    if not {'age','equity','fin','liq','norminc','levratio','y1','yy1','wgt'}.issubset(df.columns):
        raise ValueError('Colonnes SCF attendues absentes.')
    df.to_parquet(dossier/'scfp2022.parquet',index=False)
    manifeste={'url':URL,'sha256_zip':hashlib.sha256(archive.read_bytes()).hexdigest(),'lignes':len(df),'colonnes':len(df.columns)}
    (RACINE/'reports/source_scf.json').write_text(json.dumps(manifeste,indent=2))
    print('Données SCF préparées :',len(df),'lignes.')

if __name__=='__main__':main()
