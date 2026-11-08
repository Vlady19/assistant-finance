# Comparaison SCF — parcours clarifié, 29 septembre 2026

L'utilisateur a signalé que les ratios demandés n'étaient pas compréhensibles : une somme pouvait être saisie comme un nombre de mois, ou une mensualité comme une proportion d'endettement. Cette évolution corrige la collecte et la présentation, en conservant le modèle existant.

## Parcours livré

1. Décrire son épargne et obtenir l'analyse habituelle.
2. Choisir explicitement de se comparer à des ménages américains de l'enquête 2022, ou ignorer cette étape.
3. Saisir l'âge et des montants en euros, pour un périmètre de foyer cohérent.
4. Voir quatre distributions, un trait orange « Vous » et une médiane verte ; télécharger le graphique si souhaité.

Aucun appel LLM n'est nécessaire pour cette comparaison. Les montants de ce formulaire ne sont pas ajoutés au profil servant de mémoire au chatbot.

## Informations demandées

| Saisie | Calcul Python |
|---|---|
| Âge | Âge |
| Épargne et placements + montant investi en actions | Actions / épargne financière |
| Argent disponible + revenus mensuels habituels avant impôt | Liquidités / revenu mensuel |
| Valeur des biens, avant déduction des dettes + capital restant dû | Dettes / actifs totaux |

Exemple fictif : 6 000 € disponibles et 3 000 € de revenu donnent 2 mois de revenu. Les contrôles rejettent les divisions par zéro et les totaux incohérents. Un résultat précédent est effacé si une nouvelle saisie est invalide.

## Présentation et méthode

Les 4 532 ménages exploitables sont les mêmes que dans le protocole de clustering. Les distributions, médianes et positions utilisent les observations brutes, non pondérées. Le dernier intervalle des histogrammes regroupe la queue de distribution, avec une borne marquée « + ». Le repère de l'utilisateur n'est jamais tronqué : l'axe s'étend si nécessaire.

Le rang affiché est la proportion de ménages de cet échantillon dont la part en actions est inférieure **ou égale** à celle de l'utilisateur ; les ex æquo sont donc explicitement inclus. Il ne s'agit pas d'un percentile pondéré représentatif de tous les Américains.

Les informations techniques (distance, identifiant de groupe, variables internes et empreinte du modèle) restent accessibles dans un volet de détails. L'affichage principal emploie des phrases courtes. La barre latérale utilise des libellés français, des euros et des durées, plutôt que les noms de champs et les valeurs booléennes Python.

Le groupe issu du clustering est encore calculé par le modèle V6. Ses moyennes utilisent les plafonds d'entraînement, contrairement aux médianes descriptives brutes ; cette différence est expliquée dans le volet méthodologique. Un profil trop éloigné ne reçoit pas de groupe, mais conserve son graphique de comparaison.

## Fichiers concernés

- `app_streamlit.py` : profil initial allégé, invitation après analyse, choix facultatif, barre latérale lisible.
- `app/pipeline.py` : option permettant de ne pas calculer ou afficher le SCF dans le parcours de base.
- `app/comparaison_scf.py` : validation des montants, ratios, données, positions et histogrammes.
- `app/vue_comparaison.py` : formulaire facultatif, résultat, graphique et téléchargement.
- `tests/test_interface.py` : parcours acceptation/refus, saisie invalide, rendu, absence de calcul automatique et isolation de la mémoire LLM.
- `tests/test_comparaison_scf.py` : conversions, dénominateurs, cohérence, médianes, ex æquo et repères hors plage habituelle.
- `README.md` : documentation du nouveau parcours.

## Validation

La suite locale complète comporte **41 tests réussis**. Elle comprend les tests existants et les contrôles ajoutés pour cette évolution. Les campagnes API historiques n'ont pas été relancées : les prompts et règles de classification ne sont pas modifiés.

Le démarrage Streamlit et le parcours complet ont également été vérifiés dans le navigateur, avec des données fictives : analyse initiale, choix volontaire, saisie des montants, graphique et groupe calculé.

L'entraînement, le modèle sauvegardé et les allocations pédagogiques ne sont pas changés par cette évolution.

## Source et limite

[Federal Reserve — SCF 2022](https://www.federalreserve.gov/econres/scfindex.htm). Le revenu de l'enquête est mesuré avant impôt : [rapport officiel](https://www.federalreserve.gov/publications/october-2023-changes-in-us-family-finances-from-2019-to-2022.htm). Les différences de pays, de systèmes de retraite et de conventions de patrimoine limitent la comparaison ; elle reste descriptive, sans note ni objectif financier imposé.
