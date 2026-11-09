# Données SCF

Ce dossier contient les sources publiques utilisées pour l'exploration,
l'entraînement et la comparaison descriptive avec les ménages du SCF 2022.

Le sous-dossier [raw](raw/README.md) décrit l'archive officielle et son export
Parquet. Les scripts ne stockent pas les profils saisis dans l'interface ici.

La préparation est effectuée par `app/preparer_donnees.py`. La sélection des
familles et le calcul des quatre variables sont définis dans `app/entrainement.py`.
