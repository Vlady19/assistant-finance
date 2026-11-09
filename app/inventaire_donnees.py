"""Télécharge ou charge le SCF 2022, puis décrit son contenu.
Affiche les colonnes, valeurs manquantes, imputations et poids d'enquête, sans entraîner de modèle.
"""


import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

# Extrait synthétique officiel du SCF 2022, contenant les agrégats financiers.

URL = "https://www.federalreserve.gov/econres/files/scfp2022s.zip"

DOSSIER_BRUT = Path("data/raw")
FICHIER_LOCAL = DOSSIER_BRUT / "scfp2022.parquet"


def telecharger() -> pd.DataFrame:
    """Charge le Parquet en cache ou récupère le ZIP SCF et extrait ses données Stata."""

    DOSSIER_BRUT.mkdir(parents=True, exist_ok=True)

    if FICHIER_LOCAL.exists():
        print(f"Cache trouvé : {FICHIER_LOCAL}")
        return pd.read_parquet(FICHIER_LOCAL)

    zip_local = DOSSIER_BRUT / "scfp2022s.zip"

    if zip_local.exists():
        # Réutiliser l'archive locale évite un nouveau téléchargement.
        print(f"Archive locale trouvée : {zip_local}")
        contenu = zip_local.read_bytes()
    else:
        print(f"Téléchargement depuis {URL}")

        # Le User-Agent est précisé pour la requête vers l'archive publique.
        requete = urllib.request.Request(
            URL,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )

        with urllib.request.urlopen(requete, timeout=120) as reponse:
            contenu = reponse.read()

        zip_local.write_bytes(contenu)  # on garde l'archive brute

    print(f"Archive : {len(contenu) / 1_000_000:.1f} Mo")

    with zipfile.ZipFile(io.BytesIO(contenu)) as archive:
        noms = archive.namelist()
        print(f"Contenu de l'archive : {noms}")
        nom_dta = next(n for n in noms if n.lower().endswith(".dta"))
        with archive.open(nom_dta) as flux:
            df = pd.read_stata(flux, convert_categoricals=False)

    print(f"Mise en cache dans {FICHIER_LOCAL}")
    df.to_parquet(FICHIER_LOCAL)
    return df


def decrire(df: pd.DataFrame) -> None:
    """Affiche les dimensions, les imputations, les poids et les statistiques des colonnes."""

    print("\n" + "=" * 70)
    print("  DIMENSIONS")
    print("=" * 70)
    print(f"  Lignes   : {len(df):,}")
    print(f"  Colonnes : {df.shape[1]}")
    print(f"  Mémoire  : {df.memory_usage(deep=True).sum() / 1_000_000:.0f} Mo")

    # Une famille possède cinq versions imputées : yy1 identifie la famille,
    # y1 sa version. Le protocole ML sélectionne un implicat pour éviter les doublons.

    print("\n" + "=" * 70)
    print("  STRUCTURE DES IMPUTATIONS MULTIPLES")
    print("=" * 70)

    if {"yy1", "y1"}.issubset(df.columns):
        familles = df["yy1"].nunique()
        print(f"  Familles distinctes (yy1)     : {familles:,}")
        print(f"  Lignes par famille (moyenne)  : {len(df) / familles:.1f}")
        print(f"  Valeurs distinctes de y1       : {df['y1'].nunique()}")
        print("\n  → Chaque famille apparaît plusieurs fois. À traiter.")
    else:
        print("  Colonnes yy1 / y1 absentes : structure à vérifier manuellement.")

    # Les poids wgt permettent de distinguer les statistiques de l'échantillon
    # des estimations de population ; leur présence est décrite ici.

    print("\n" + "=" * 70)
    print("  PONDÉRATIONS")
    print("=" * 70)

    if "wgt" in df.columns:
        print(df["wgt"].describe().to_string())
        print("\n  → Poids de sondage présents. Leur usage est une décision à prendre.")
    else:
        print("  Colonne wgt absente.")

    # Inventaire des types et des valeurs manquantes, colonne par colonne.

    print("\n" + "=" * 70)
    print("  COLONNES (nom, type, valeurs manquantes, exemple)")
    print("=" * 70)

    for nom in df.columns:
        serie = df[nom]
        manquants = serie.isna().sum()
        taux = manquants / len(df) * 100
        exemple = serie.dropna().iloc[0] if manquants < len(serie) else "—"
        print(f"  {nom:<18} {str(serie.dtype):<10} "
              f"manquants {taux:>5.1f} %   ex. {exemple}")

    # Statistiques descriptives des principaux agrégats financiers.

    print("\n" + "=" * 70)
    print("  APERÇU NUMÉRIQUE (colonnes les plus utiles a priori)")
    print("=" * 70)

    # Liste indicative à interpréter avec le dictionnaire officiel de l'enquête.
    attendues = [
        "age", "income", "norminc", "networth", "asset", "debt",
        "fin", "nfin", "liq", "stocks", "bond", "nmmf", "retqliq",
        "houses", "educ", "married", "kids", "saved",
    ]
    presentes = [c for c in attendues if c in df.columns]
    absentes = [c for c in attendues if c not in df.columns]

    if presentes:
        print(df[presentes].describe().T.to_string())
    if absentes:
        print(f"\n  Non trouvées : {', '.join(absentes)}")
        print("  → à retrouver dans le codebook, elles portent un autre nom.")


if __name__ == "__main__":
    donnees = telecharger()
    decrire(donnees)

    print("\n" + "=" * 70)
    print("  Inventaire SCF terminé.")
    print("  Préparation des données : python -m app.preparer_donnees")
    print("  Entraînement du modèle : python -m app.entrainement")
    print("=" * 70 + "\n")
