# Bilan technique de la validation initiale

Ce document décrit les corrections et la validation effectuées le 28 septembre
2026, avec un bilan finalisé le 29 septembre. Les résultats sont historiques.
L'évolution suivante du formulaire SCF, validée par 41 tests locaux, est décrite
dans [evolution_comparaison_scf.md](evolution_comparaison_scf.md).

## Périmètre

La validation initiale porte sur le parcours conversationnel, les règles Python,
l'intégration du clustering, les contrôles de rédaction et l'interface Streamlit.
L'application reste pédagogique : les règles d'allocation sont fixes et la
comparaison SCF est descriptive.

## Principales corrections

| Point traité | Résultat |
|---|---|
| Points d'entrée incohérents | Le terminal et Streamlit utilisent le même orchestrateur `app.pipeline`. |
| Calculs mélangés à la rédaction | Les valeurs viennent de Python ; le LLM fournit une explication contrôlée. |
| Profil incomplet ou invalide | Pydantic contrôle les valeurs ; les informations manquantes restent à `None` et les zéros sont conservés. |
| Observations SCF confondues avec le risque déclaré | Les quatre variables observées sont séparées de la tolérance et de la précaution en mois de dépenses. |
| Clustering non traçable | Le modèle enregistré est appelé avec des entrées, une distance, un statut et une empreinte visibles. |
| Modèle absent, corrompu ou profil éloigné | Le statut explicite remplace toute attribution de secours. |
| API absente ou rédaction invalide | Le formulaire reste local ; un texte de secours et des erreurs lisibles sont disponibles. |
| Collecte bloquant les autres questions | Une demande pédagogique peut interrompre la collecte tout en conservant le profil. |
| Allocation malgré des contraintes incompatibles | L'illustration est suspendue selon les seuils d'horizon et de précaution du projet. |
| Dépendances et données peu documentées | Versions fixées, script de préparation, protocole ML et rapports conservés. |

## Résultats enregistrés

| Vérification | Résultat de la campagne | Fichier de référence |
|---|---|---|
| Suite locale initiale | 32 tests réussis | `tests_complets.log` |
| Classification API, jeu initial | 21 cas réussis sur 21 | `evaluation_classification.json` |
| Classification API, jeu complémentaire | 14 cas réussis sur 14 | `evaluation_classification.json` |
| Extractions et parcours API | 12 cas réussis sur 12 | `evaluation_parcours.json` |
| Dépendances | Aucun conflit détecté dans l'environnement vérifié | `dependances_verification.txt` |
| Inférence locale sur profil fictif | Calculs et comparaison ML enregistrés | `exemple_inference.json` |
| Évolution ultérieure du formulaire SCF | 41 tests réussis | `tests_comparaison_scf.log` |

L'installation dans un environnement neuf, le démarrage Streamlit et un parcours
dans le navigateur ont également été vérifiés pendant la validation initiale.
Ces résultats ne remplacent pas une nouvelle exécution sur une autre installation.

Les campagnes API portent sur des scénarios fictifs. Les références d'extraction
et les montants attendus sont définis séparément des réponses du modèle. Les cas
déjà inspectés constituent des régressions connues, pas une évaluation aveugle.

## Résultats ML

- Premier implicat : 4 595 familles, dont 4 532 retenues et 63 exclues.
- Séparation par famille : 3 625 observations train et 907 observations test.
- Scaler ajusté uniquement sur train, avec une vérification indépendante des moyennes.
- Silhouette train : 0,261 pour K=2, 0,295 pour K=3 et 0,338 pour K=4.
- Modèle retenu : K=3 pour la lisibilité et la continuité de l'interprétation,
  malgré une meilleure silhouette de K=4 dans cette comparaison.
- Silhouette test de K=3 : 0,312.
- Stabilité sur trois autres initialisations : ARI entre 0,962 et 1,000.
- Profils test au-delà du seuil de distance : environ 1,43 %.

Les détails sont conservés dans `protocole_ml.json` et `predictions_test.json`.
Le seuil de distance est une heuristique d'abstention, pas une probabilité de fiabilité.

## Limites et suites possibles

Les allocations sont des illustrations fondées sur des règles fixes. Le SCF ne
démontre pas qu'elles sont optimales. L'entraînement utilise un seul implicat
et ne pondère pas K-Means avec les poids d'enquête ; leur effet est étudié
uniquement dans une comparaison descriptive. Aucune validation externe française
n'est fournie.

Les contrôles lexicaux réduisent certains risques de rédaction sans prouver la
vérité de chaque phrase. La mémoire conserve surtout le profil structuré.
Le projet utilise des fonctions Python prédéfinies, sans LangChain ni exécution
de code généré par le LLM. Aucune source de marché en direct ou base fiscale
actualisée n'est connectée.

À la date de ce bilan, le script de reconstruction des données était fourni,
mais sa reconstruction complète restait à vérifier séparément. Les tests
enregistrés utilisaient les données et le modèle déjà disponibles.

Les pistes d'amélioration comprennent de nouveaux cas d'évaluation indépendants,
des campagnes API répétées et une étude plus large de K, des plafonds, des poids
et des imputations.
