# Modèles enregistrés

| Fichier | Rôle |
|---|---|
| `segmentation.joblib` | Modèle actif : pipeline de bornage, StandardScaler, K-Means, seuil de distance et provenance. |
| `kmeans.joblib` | Archive du modèle de clustering initial, non chargée par l'application. |
| `scaler.joblib` | Archive du scaler initial, non chargée par l'application. |
| `noms_clusters.joblib` | Anciens libellés des groupes, non utilisés pour interpréter le modèle actif. |

`app/entrainement.py` génère le modèle actif. `app/clustering.py` le charge pour
la comparaison, calcule une distance et écarte les profils au-delà du seuil.
Le groupe décrit une ressemblance statistique et ne détermine pas l'allocation.

Le contenu des fichiers Joblib est binaire. Leur rôle est documenté ici sans
modifier les artefacts enregistrés.
