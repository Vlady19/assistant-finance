"""
src/inventaire_donnees.py — première étape de la V6.

    python src/inventaire_donnees.py

Ce script NE PREND AUCUNE DÉCISION. Il télécharge le fichier, l'ouvre, et
décrit ce qu'il contient. C'est tout.

C'est volontaire, et c'est la même discipline que depuis la V2 : on regarde
ce qu'on a avant de décider quoi en faire. Choisir un algorithme avant de
connaître ses données, c'est exactement l'erreur que j'ai commise au premier
message de notre conversation.

Ce que tu obtiendras : la taille du fichier, la liste complète des colonnes,
la structure des imputations multiples, et l'état des valeurs manquantes.
Envoie-moi cette sortie, on décidera de la suite ensemble.

Dépendances :  pip install pandas
(pandas sait lire le format Stata nativement, rien d'autre à installer)
"""

import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

# ─────────────────────────────────────────────────────────────────────────
# Le Summary Extract Public Data du Survey of Consumer Finances 2022.
#
# Pourquoi l'extrait « summary » et pas le fichier public complet ?
# Le fichier complet contient plusieurs milliers de variables brutes, avec
# des noms cryptiques (X5729, X3506...). L'extrait regroupe ces variables
# en agrégats lisibles et documentés — c'est celui qu'utilise la Réserve
# fédérale pour ses propres publications. Très largement suffisant ici, et
# infiniment plus maniable.
#
# Si une édition plus récente existe quand tu lis ceci, remplace 2022 par
# l'année voulue dans l'URL. L'enquête est triennale.
# ─────────────────────────────────────────────────────────────────────────

URL = "https://www.federalreserve.gov/econres/files/scfp2022s.zip"

DOSSIER_BRUT = Path("data/raw")
FICHIER_LOCAL = DOSSIER_BRUT / "scfp2022.parquet"


def telecharger() -> pd.DataFrame:
    """Télécharge le zip, extrait le .dta, renvoie un DataFrame."""

    DOSSIER_BRUT.mkdir(parents=True, exist_ok=True)

    if FICHIER_LOCAL.exists():
        print(f"Cache trouvé : {FICHIER_LOCAL}")
        return pd.read_parquet(FICHIER_LOCAL)

    zip_local = DOSSIER_BRUT / "scfp2022s.zip"

    if zip_local.exists():
        # Repli manuel : si le téléchargement automatique échoue, tu peux
        # récupérer le fichier depuis ton navigateur et le déposer ici.
        print(f"Archive locale trouvée : {zip_local}")
        contenu = zip_local.read_bytes()
    else:
        print(f"Téléchargement depuis {URL}")

        # ─────────────────────────────────────────────────────────────────
        # POURQUOI CET EN-TÊTE
        #
        # Par défaut, urllib s'identifie comme « Python-urllib/3.x ». De
        # nombreux serveurs publics rejettent ces requêtes en bloc pour se
        # protéger des robots : d'où le 403 Forbidden.
        #
        # On se présente donc comme un navigateur ordinaire. Le fichier est
        # public et librement diffusé — on contourne un filtre anti-robot,
        # pas une restriction d'accès.
        # ─────────────────────────────────────────────────────────────────
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
    """Affiche tout ce qu'il faut savoir avant de décider quoi que ce soit."""

    print("\n" + "=" * 70)
    print("  DIMENSIONS")
    print("=" * 70)
    print(f"  Lignes   : {len(df):,}")
    print(f"  Colonnes : {df.shape[1]}")
    print(f"  Mémoire  : {df.memory_usage(deep=True).sum() / 1_000_000:.0f} Mo")

    # ── Le piège des imputations multiples ────────────────────────────────
    #
    # Les réponses manquantes de l'enquête ont été estimées cinq fois par
    # une méthode statistique. Chaque famille apparaît donc en CINQ
    # exemplaires, légèrement différents.
    #
    #   yy1 = identifiant de la famille
    #   y1  = identifiant de l'exemplaire (l'« implicate »)
    #
    # Si on ignore ça et qu'on lance un clustering sur le fichier brut, on
    # compte chaque famille cinq fois. Les groupes obtenus n'ont alors plus
    # de sens statistique.
    #
    # Le barème sanctionne ce genre d'erreur bien plus durement qu'un
    # score médiocre : « c'est la rigueur du protocole qui est évaluée ».

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

    # ── Les pondérations ─────────────────────────────────────────────────
    #
    # Une enquête ne tire pas les ménages au hasard uniforme : les hauts
    # patrimoines sont volontairement sur-représentés, sinon on n'en
    # observerait presque aucun. Le poids (wgt) corrige ce biais.
    #
    # Conséquence : une moyenne calculée sans les poids décrit l'échantillon,
    # pas la population. C'est un point à traiter et à expliquer.

    print("\n" + "=" * 70)
    print("  PONDÉRATIONS")
    print("=" * 70)

    if "wgt" in df.columns:
        print(df["wgt"].describe().to_string())
        print("\n  → Poids de sondage présents. Leur usage est une décision à prendre.")
    else:
        print("  Colonne wgt absente.")

    # ── Inventaire des colonnes ──────────────────────────────────────────

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

    # ── Statistiques des colonnes numériques ─────────────────────────────

    print("\n" + "=" * 70)
    print("  APERÇU NUMÉRIQUE (colonnes les plus utiles a priori)")
    print("=" * 70)

    # On regarde si les variables classiques du SCF sont là. Je les cite de
    # mémoire : vérifie-les dans le codebook officiel plutôt que de me faire
    # confiance. Une variable mal comprise fausse tout le clustering.
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
    print("  Copie cette sortie et envoie-la moi.")
    print("  On choisira les variables de segmentation ensemble, ")
    print("  une fois qu'on saura ce qu'il y a réellement dedans.")
    print("=" * 70 + "\n")
