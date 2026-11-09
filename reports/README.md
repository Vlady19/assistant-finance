# Rapports et résultats de validation

Ce dossier conserve les résultats produits par les scripts du projet.
Les JSON restent lisibles par les programmes et les journaux gardent les sorties
des campagnes correspondantes.

| Fichier ou groupe | Contenu |
|---|---|
| `protocole_ml.json` | Familles train/test, comparaison de K, silhouette, stabilité, seuil et empreinte du modèle. |
| `predictions_test.json` | Groupe, distance et acceptation de l'attribution pour chaque profil test. |
| `eda.json` | Qualité des données, définition des variables et corrélations. |
| `evaluation_classification.json` | Réponses et scores de classification avec appels API, séparés par jeu de cas. |
| `evaluation_parcours.json` | Résultats API des extractions, parcours et dialogue à plusieurs tours. |
| `exemple_inference.json` | Analyse locale enregistrée pour le profil fictif fourni dans `examples/`. |
| `source_scf.json`, si généré | Provenance, empreinte du ZIP et dimensions des données préparées. |
| `entrainement.log` | Sortie enregistrée d'un entraînement. |
| `tests_comparaison_scf.log` | Campagne de 41 tests incluant le formulaire et les graphiques SCF. |
| `tests_complets.log` et `tests_phase_*.log` | Campagnes antérieures, avec un périmètre de tests propre à chaque journal. |
| `dependances_verification.txt` | Résultat du contrôle de cohérence des dépendances. |
| `bilan_reprise.md` | Bilan technique historique et limites de la première validation. |
| `evolution_comparaison_scf.md` | Description de l'évolution du parcours SCF et de sa validation. |
| [figures](figures/README.md) | Distributions SCF et comparaison des silhouettes. |

Ces fichiers décrivent une campagne donnée, pas l'état automatiquement actualisé
du code. Les scores API ne garantissent pas la justesse de toutes les réponses.
La commande de test et les points d'entrée actuels sont indiqués dans le README
principal et dans les en-têtes des scripts.
