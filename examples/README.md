# Profil d'exemple

`profil_complet.json` décrit une situation fictive utilisable avec
`python infer.py examples/profil_complet.json` depuis la racine du projet.

Les cinq informations principales définissent le capital, l'horizon, la tolérance
au risque, la précaution en mois de dépenses et la résidence fiscale française.
Les quatre observations supplémentaires servent à la comparaison SCF :

- `age` : âge en années.
- `part_actions_actuelle` : part d'actions dans l'épargne financière, entre 0 et 1.
- `liquidites_mois_revenu` : liquidités divisées par le revenu mensuel habituel.
- `ratio_dette_actifs` : dettes divisées par la valeur totale des actifs.

Les valeurs sont validées par `app/models.py`. Un ratio de `0.43` signifie
43 %, et les mois de revenu sont distincts des mois de dépenses.
