# Sources brutes du SCF 2022

Les données proviennent de la [Federal Reserve](https://www.federalreserve.gov/econres/scfindex.htm).

| Fichier | Rôle |
|---|---|
| `scfp2022s.zip` | Cache de l'archive officielle contenant l'extrait synthétique Stata. |
| `scfp2022.parquet` | Export numérique lu par l'entraînement, l'exploration et la comparaison SCF. |

Préparation depuis la racine du projet : `python -m app.preparer_donnees`.
Si le téléchargement automatique échoue, l'archive officielle peut être placée
ici sous le nom `scfp2022s.zip`.

Le fichier brut contient les différentes imputations de l'enquête. La sélection
du premier implicat et le filtrage des ratios invalides ont lieu dans
`app/entrainement.py`. Les fichiers de données sont exclus de Git ; ce README
documente leur préparation.
