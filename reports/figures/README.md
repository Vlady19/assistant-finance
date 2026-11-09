# Figures de l'exploration SCF

`notebooks/eda_clustering.py` génère les deux images de ce dossier :

- `eda_exploration.png` : distributions de l'âge et des trois ratios financiers
  sur les ménages retenus, avec les plafonds indiqués sur les graphiques.
- `silhouette_scores.png` : comparaison des scores train pour K égal à 2, 3 et 4,
  à partir de `reports/protocole_ml.json`.

Ces images documentent l'exploration et le protocole. Le graphique individuel
affiché par Streamlit est calculé séparément par `app/comparaison_scf.py`.
