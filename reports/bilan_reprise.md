# Livraison de la reprise V6 — 29 septembre 2026

> Bilan historique de la première livraison. Une évolution ultérieure du parcours SCF, avec 41 tests locaux réussis, est décrite dans [evolution_comparaison_scf.md](evolution_comparaison_scf.md).

**La copie de travail fonctionne, le clustering est effectivement intégré et les tests enregistrés sont concluants.** Cette livraison reprend le projet existant ; elle ne remplace pas son architecture par un système d'agents plus complexe. L'application reste un assistant pédagogique d'investissement, avec une comparaison statistique descriptive.

Les corrections et validations ont été réalisées le 28 septembre. Le 29 septembre, seuls ce bilan, l'inventaire et l'archive de livraison ont été finalisés. Aucun nouvel audit ni nouvelle campagne de tests n'a été lancé à cette occasion.

## Où travailler

- Projet corrigé : `outputs/assistant-finance/` dans cet espace Codex.
- Projet d’origine, non réécrit par cette reprise : `/Users/dimitri/pdf-text-modifier/Python/assistant-finance`.
- Copie initiale conservée : `work/recuperation/projet_local/`.
- Téléchargements historiques Claude : `work/recuperation/claude/`.
- Archive livrée : `outputs/assistant-finance-v6.zip` ; elle contient le code, les modèles, les données SCF publiques et les rapports, sans clé API, environnement virtuel ni caches.

Le manifeste `inventaire_livraison.json` énumère les fichiers livrés, leur état par rapport à la copie initiale et leur empreinte SHA-256. Il permet de distinguer les fichiers réellement modifiés des fichiers conservés.

**Contrôle d'intégrité de livraison :** les 28 fichiers de la sauvegarde initiale correspondent à leurs empreintes enregistrées. Dans le projet d'origine, 27 correspondent et `app/regles.py` diffère aujourd'hui de cette sauvegarde. La cause de cette différence n'a pas été recherchée dans cette phase de livraison. Ce fichier n'a été ni écrasé ni fusionné avec la copie corrigée ; continuer le travail dans `outputs/assistant-finance/` évite toute ambiguïté.

## Changements effectués

| Problème initial | Correction effective | Effet pour la démonstration |
|---|---|---|
| Import Streamlit de `pipelineV4`, fichier absent | Utilisation de `app.pipeline` ; terminal aligné sur le même orchestrateur | L'interface démarre et les deux interfaces suivent la même logique |
| Validateur remplacé par un rejet systématique de test | Contrôles actifs, une nouvelle tentative, puis réponse de secours | Les réponses valides passent ; les échecs restent visibles |
| Un nombre du dossier pouvait être recyclé avec un autre sens | Explication qualitative du LLM ; valeurs affichées séparément par Python | Un horizon ne peut plus autoriser un rendement chiffré dans la prose libre |
| Explication attribuant à l'âge un effet sur les règles d'allocation | Informations SCF et message brut retirés de l'entrée du rédacteur des règles | La comparaison descriptive ne devient pas une fausse justification d'allocation |
| Clé manquante bloquant l'import de l'application | Client chargé à la demande ; erreur lisible ; formulaire local sans API | L'application reste démontrable sans réseau ni clé |
| Erreurs API mal maîtrisées | Délai d'attente, reprises bornées, profil conservé, résultats Python disponibles si la rédaction échoue | Dégradation explicite et utile |
| Valeurs négatives ou non finies acceptées | Contraintes Pydantic sur capital, horizon, âge et ratios | Les données invalides sont refusées avant le calcul |
| `profil.age` inexistant dans les fichiers V6 | Ajout cohérent de quatre observations facultatives dans `Profil`, extraction et formulaire | Pas d'âge moyen inventé ni de dette supposée nulle |
| Tolérance déclarée assimilée à une détention d'actions | Champs distincts pour préférence et situation observée | Même sens des données à l'entraînement et à l'utilisation |
| Mois de dépenses assimilés aux mois de revenu du SCF | Deux champs distincts, libellés explicites | Comparaison statistique interprétable |
| ML absent du parcours ou remplacé silencieusement | Appel réel au pipeline sauvegardé ; statut, distance, empreinte et entrées visibles | Preuve de l'utilisation du modèle |
| Modèle absent, corrompu ou profil très éloigné | Statuts d'indisponibilité ou de non-attribution, sans faux segment par défaut | Limites visibles et testées |
| Question de choix entre indices classée en allocation | Définition générale du choix d'instruments nommés, distinguée de l'allocation et de la comparaison descriptive | Correction du cas S&P 500/MSCI World sans exemple spécial dans le prompt |
| Toute réponse pendant une collecte forcée vers l'allocation | Classification tenant compte de la dernière question sans bloquer un changement de sujet | Dialogue interrompu puis repris sans perte du profil |
| Allocation illustrative malgré horizon très court ou précaution insuffisante | Suspension de l'illustration selon les règles du projet | Cohérence entre alerte et résultat affiché |
| Dépendances absentes du livrable | Fichier de versions verrouillées et installation dans un environnement neuf | Reproductibilité nettement améliorée |

Les répartitions historiques restent des **règles pédagogiques fixes**. Les moyennes observées dans les clusters ne sont pas transformées en recommandations d'investissement : le clustering décrit une population, il ne démontre pas une allocation optimale.

## Fichiers modifiés et ajoutés

Les chemins de ce tableau sont relatifs à la racine du projet corrigé. L'inventaire JSON donne le détail fichier par fichier, y compris les rapports.

| Fichiers | État | Rôle des changements |
|---|---|---|
| `app_streamlit.py`, `main.py` | Modifiés | Interface, orchestrateur commun, formulaire local, conservation des résultats et traces |
| `app/models.py`, `app/conversation.py` | Modifiés | Données contraintes, observations SCF facultatives, mémoire compatible avec les profils historiques |
| `app/config.py`, `app/llm.py`, `app/intents.py` | Modifiés | Client à la demande, extraction, classification contextualisée, données de marché indisponibles |
| `app/pipeline.py`, `app/regles.py` | Modifiés | Calcul central, appel ML effectif, contrôle des prérequis, provenance des résultats |
| `app/redaction.py`, `app/validation.py` | Modifiés | Explication qualitative, contrôle, nouvelle tentative, secours |
| `app/features.py`, `app/clustering.py` | Ajoutés | Préparation commune et inférence ML avec statuts explicites |
| `app/entrainement.py` | Ajouté | Séparation des familles, pipeline complet, comparaison des configurations et stabilité |
| `models/segmentation.joblib` | Ajouté | Modèle réellement chargé par l'application |
| `app/preparer_donnees.py`, `data/raw/README.md` | Ajoutés | Reconstruction des données depuis le ZIP officiel ou son cache ; commande encore à valider séparément |
| `notebooks/eda_clustering.py` | Modifié | Définitions corrigées, EDA séparée de l'entraînement et figures mises à jour |
| `evals/lancer.py` | Modifié | Évaluation de classification avec résultats persistés |
| `evals/cas_generalisation.py`, `evals/parcours.py` | Ajoutés | Cas complémentaires, extraction et parcours API synthétiques |
| `tests/test_demarrage.py`, `tests/test_interface.py`, `tests/test_v6.py` | Ajoutés | Démarrage, parcours, profil et utilisation du ML |
| `tests/test_protocole_ml.py`, `tests/test_redaction.py` | Ajoutés | Absence de fuite, référence indépendante de distance, modèles corrompus, rédaction |
| `infer.py`, `examples/profil_complet.json` | Ajoutés | Inférence hors interface et exemple fictif réutilisable |
| `lancer_local.py` | Ajouté | Démarrage local avec un `.env` externe facultatif, sans copier la clé |
| `requirements.txt`, `.env.example`, `.gitignore`, `README.md` | Modifiés | Installation, configuration, exclusions et documentation pédagogique |
| `requirements-lock.txt` | Ajouté | Versions exactes de l'environnement validé |
| `reports/figures/eda_exploration.png`, `reports/figures/silhouette_scores.png` | Modifiés | Graphiques issus du protocole corrigé |
| Rapports JSON et journaux dans `reports/` | Ajoutés | Preuves de tests, protocole, inférence et prédictions test |

Les trois modèles historiques séparés et les 21 questions historiques ont été conservés. L'application utilise désormais le nouveau fichier `segmentation.joblib`, contenant la préparation et KMeans ensemble.

## État final des tests enregistrés

| Vérification | Résultat | Preuve |
|---|---|---|
| Suite locale complète, dans le nouvel environnement | **32/32**, aucune erreur | `tests_complets.log` |
| Classification API, jeu historique | **21/21** ; auparavant 20/21 | `evaluation_classification.json` |
| Classification API, 14 cas complémentaires | **14/14** | Même rapport, groupe `generalisation` |
| Extractions et parcours API | **12/12** : 5 extractions, 6 parcours, 1 dialogue à plusieurs tours | `evaluation_parcours.json` |
| Questions des deux jeux recopiées littéralement dans le prompt | **0** | Rapport de classification |
| Installation des dépendances dans un environnement neuf | Réussie | Journal d'installation conservé dans le dossier de travail |
| Cohérence des dépendances installées | Aucun conflit détecté | `dependances_verification.txt` |
| Inférence autonome sur profil fictif | Résultat enregistré avec clustering utilisé | `exemple_inference.json` |
| Démarrage réel de Streamlit | Serveur démarré, contrôle de santé `ok` | Exécution réalisée pendant la correction |
| Parcours réel dans le navigateur | Formulaire → calculs Python → segment SCF affiché | Capture `outputs/apercu_application.png` |

Les tests couvrent notamment : absence de clé, erreur de rédaction, nouvelle tentative, données invalides, zéro préservé, observations facultatives, modèle absent ou corrompu, indépendance du dossier courant, séparation tolérance/segment, profils éloignés, changement de sujet, cours indisponible, formulaire incomplet, historique et réinitialisation.

Ces nombres évaluent des périmètres distincts. **Ils ne prouvent pas que toutes les réponses possibles du chatbot sont correctes.** Une réponse finale correcte a nécessité une nouvelle tentative du rédacteur dans la dernière campagne ; ce contrôle est enregistré. Les vérifications automatiques des parcours portent surtout sur le routage, les données structurées et les calculs, pas sur une validation exhaustive de chaque phrase. Les jeux déjà inspectés sont désormais des tests de régression. Une évaluation aveugle sur de nouvelles questions, répétée plusieurs fois, reste souhaitable.

### Résultats ML

- 4 595 familles dans le premier implicat ; 4 532 retenues, 63 exclues pour les règles de validité des observations.
- 3 625 familles pour l'entraînement et 907 pour le test, sans chevauchement.
- Scaler ajusté sur l'entraînement seulement ; le test indépendant vérifie sa moyenne contre une référence pandas.
- Silhouette train : **0,261 pour k=2**, **0,295 pour k=3**, **0,338 pour k=4**.
- Silhouette test du modèle conservé à trois groupes : **0,312**.
- Stabilité des attributions test selon trois autres graines : ARI entre **0,962 et 1,000**.
- Environ **1,43 %** des observations test dépassent le seuil de distance retenu et ne reçoivent pas d'attribution acceptée.

Trois groupes sont conservés pour la continuité du projet et sa lisibilité. Ce choix est assumé ; il n'est pas présenté comme l'optimum de silhouette. Le rejet par distance est une heuristique, pas une probabilité de fiabilité. Les fichiers `protocole_ml.json` et `predictions_test.json` contiennent les résultats détaillés.

## Lancement sur cette machine

L'environnement neuf existe déjà dans le projet corrigé. Depuis un terminal :

```bash
cd "/Users/dimitri/Documents/Codex/2026-09-28/oui-je-te-conseille-de-donner/outputs/assistant-finance"
.venv/bin/python lancer_local.py --env-file "/Users/dimitri/pdf-text-modifier/Python/assistant-finance/.env"
```

Ouvrir ensuite `http://127.0.0.1:8501`. L'option `--port 8503` permet de choisir un autre port si nécessaire. Aucun besoin de réinstaller les dépendances sur cette copie.

Sans accès à une clé API :

```bash
.venv/bin/python lancer_local.py
```

Le formulaire local calcule les règles et le clustering ; le chat signale la clé absente. Pour une autre machine ou l'archive extraite, suivre l'installation du `README.md` : créer un environnement Python 3.14 et installer `requirements.txt`. Les données et le modèle entraîné sont déjà dans l'archive ; leur réentraînement n'est pas nécessaire pour la démonstration.

La commande de reconstruction complète des données a été ajoutée, mais sa vérification finale n'a pas été exécutée avant l'interruption de la session précédente. La livraison du 29 septembre ne relance pas cette vérification, conformément à la demande. Cela ne remet pas en cause les tests effectués avec les données déjà récupérées.

## Correspondance Datagong après corrections

Ce tableau est un état de préparation, pas une note attribuée à la place du jury. L'équivalence des critères du cas de crédit doit être validée dans le contexte du projet.

| Bloc | État actuel | Reste à faire |
|---|---|---|
| A — cadrage, dépôt, reproductibilité | 🟠 README, versions verrouillées, environnement neuf, configuration et lancement documentés | Créer le véritable dépôt Git et ses commits ; tester la reconstruction des données et un démarrage depuis clone |
| B — analyse des données | 🟠 Dictionnaire utile, qualité, exclusions, ratios et figures corrigés | Mieux documenter l'effet des poids et implicats et le transfert États-Unis/France |
| C — pipeline et évaluation | 🟠 Pipeline complet, train/test par famille, contrôle de fuite et stabilité | Répétitions du protocole, sensibilité au plafonnement et aux données ; adapter officiellement les métriques de crédit |
| D — modèle et décision métier | 🟠 Comparaison de k, résultats test, inférence autonome, séparation modèle/règles et abstention | Justifier davantage k=3 ; comparer éventuellement une autre méthode ; documenter les règles métier comme hypothèses |
| E — GenAI | 🟠 Routage, extraction, calcul contrôlé, réponses de secours, traces, évaluations et Streamlit fonctionnels | Confirmer l'équivalence de l'outil Python fixe avec les exigences LangChain/exécution générée ; renforcer le golden set indépendant |
| F — rapport et qualité | 🟠 Code commenté, architecture expliquée, limites et bilan écrits | Transformer les preuves techniques en rapport de soutenance et démonstration chronométrée |

Le bloc E mérite une distinction précise :

| Exigence | Équivalent présent | Limite restante |
|---|---|---|
| E1 — agent LangChain et outil Python | Orchestrateur Python existant et fonction métier `calculer` | **LangChain absent** ; l'équivalence ne peut pas être présumée |
| E2 — exécution contrôlée | Fonctions écrites à l'avance, arguments validés, aucun `exec` de code généré | Ne remplit pas littéralement une exigence d'exécution Python générée dans un environnement isolé |
| E3 — familles de questions sur les données | Profil, allocation illustrative, comparaison d'un profil au SCF, pédagogie et limites | Pas encore d'exploration libre des agrégats SCF ni de portefeuille connecté à des données de marché |
| E4 — réponse, calcul/code, résultat | Explication séparée du rendu Python ; entrées, résultats et fonction visibles | Généraliser les preuves pour de futurs outils |
| E5 — golden set et références indépendantes | 35 classifications, 12 cas API, tests numériques et référence indépendante de distance | Tous ne sont pas des questions de calcul ; ajouter un jeu dédié d'au moins 10 questions numériques, indépendant et répété |
| E6 — refus et informations absentes | Hors périmètre, cours indisponibles, observations absentes, ML indisponible | Élargir les cas adversariaux et mesurer les refus injustifiés |
| E7 — Streamlit et historique | Fonctionnel, testé automatiquement et dans le navigateur | Répétition de la démo finale avec l'utilisateur |

Les contraintes strictement liées au défaut de crédit (cible de défaut, AUC/recall de défaut, seuil de défaut, colonnes imposées du dataset initial) ne sont pas à réintroduire artificiellement. L'équivalent pertinent porte sur la validité du protocole, la mesure de qualité et la décision d'utiliser ou de ne pas utiliser une sortie du modèle.

## Priorités avant la soutenance

| Priorité | Action | Intérêt pour le jury / lien grille | Difficulté | Fichiers concernés |
|---|---|---|---|---|
| P1 | Faire valider précisément l'adaptation de E1/E2/E3 par Guillaume | Éviter de supposer qu'une architecture fonctionnelle satisfait une technologie explicitement demandée ; bloc E, 35 points | Faible pour le cadrage ; variable pour l'ajout éventuel | Bilan, README, puis `app/pipeline.py` et outils si nécessaire |
| P1 | Formaliser un golden set numérique dédié avec références indépendantes, réponses enregistrées et plusieurs exécutions | Démontrer les calculs et l'absence d'invention au-delà du routage ; E5/E6 | Moyenne | `evals/`, `tests/`, `reports/` |
| P1 | Mettre la version en dépôt Git, créer des commits réels et vérifier le lancement depuis clone | Livrable récupérable et reproductible ; A | Faible à moyenne | `.gitignore`, README, dépendances et préparation des données |
| P2 | Approfondir les sensibilités ML : k, plafonds, poids et implicats | Défendre le modèle sans exagérer sa portée ; B/C/D/F | Moyenne | `app/entrainement.py`, EDA, `reports/` |
| P2 | Préparer un rapport court et une démo de cinq parcours, dont un échec contrôlé | Montrer les limites autant que les cas favorables ; E/F | Moyenne | Rapport de soutenance, scénario de démo, résultats existants |
| P3 | Ajouter une source financière ou un outil de calcul de portefeuille seulement si le périmètre le justifie | Élargir l'utilité sans diluer la démonstration | Moyenne à élevée | Futur module de données/outils, jeux d'évaluation dédiés |

## Formulations utiles à l'oral

« Le LLM comprend la formulation libre et extrait un profil structuré. Les calculs, les règles et les prédictions de clustering sont réalisés par Python, puis leurs résultats sont affichés avec leur provenance. »

« J'ai conservé le clustering commencé avec Claude, mais j'ai corrigé le sens des variables. Une préférence de risque n'est pas une part d'actions déjà détenues, et des mois de revenu ne sont pas des mois de dépenses. »

« Le segment décrit une ressemblance statistique avec des ménages américains. Il ne prouve pas qu'une allocation est optimale pour un épargnant français. Si une donnée manque ou si le modèle est indisponible, je le montre au lieu de fabriquer un résultat. »

« Mes tests mesurent plusieurs choses séparément : classification, extraction, calculs, intégration et interface. Le taux de classification ne suffit pas à valider la vérité de toutes les phrases du chatbot. »

## Limites de livraison et contrôles d'exécution

Aucun dépôt Git n'a encore été créé et aucun historique ancien n'a été inventé. Aucun nouveau développement applicatif n'a été ajouté pendant cette finalisation.

Le contrôle automatique avait refusé de dupliquer `.env` dans les livrables : la clé reste dans le projet d'origine et peut être chargée en mémoire avec `--env-file`. Il avait aussi refusé l'envoi d'un profil depuis le navigateur en le traitant comme des données personnelles ; le parcours navigateur a été validé avec le formulaire local sans API. Les évaluations API finales emploient des scénarios explicitement fictifs.

La session précédente avait enfin été interrompue par la limite d'utilisation lors de la préparation d'une vérification de reconstruction des données. Cette vérification n'a pas été exécutée ; elle n'est pas comptée comme réussie.
