"""Cas de validation séparés des exemples historiques, absents du prompt.

Jeu fixé avant la première exécution de la nouvelle règle de classification.
Après inspection des erreurs, il devient un jeu de régression, pas un test aveugle.
"""
from app.intents import Intent as I
CAS = [
    ("Nasdaq 100 ou Euro Stoxx 50 dans mon compte-titres ?", I.ACTIF_PRECIS, "choix d'indices, autre enveloppe"),
    ("Pour moi, je prends plutôt un ETF CAC 40 ou un fonds émergents ?", I.ACTIF_PRECIS, "choix de fonds"),
    ("Bitcoin ou Ether pour mon épargne ?", I.ACTIF_PRECIS, "choix elliptique de tokens"),
    ("Je remplace mon ETF Europe par un ETF Japon ?", I.ACTIF_PRECIS, "arbitrage explicite"),
    ("Quelles différences de composition entre le Nasdaq 100 et le CAC 40 ?", I.PEDAGOGIE, "comparaison descriptive"),
    ("Explique-moi le rôle d'un indice boursier.", I.PEDAGOGIE, "définition"),
    ("Sur quelle enveloppe détenir mes ETF, un PEA ou un CTO ?", I.FISCALITE, "choix réel de l'enveloppe"),
    ("Est-ce que les retraits de mon assurance-vie sont imposés ?", I.FISCALITE, "fiscalité"),
    ("J'ai une somme disponible, comment la partager entre actions et liquidités ?", I.ALLOCATION, "répartition générale"),
    ("Je souhaite organiser 18000 euros pour dans douze ans.", I.ALLOCATION, "objectif patrimonial"),
    ("Dois-je attendre la prochaine correction avant de placer mon argent ?", I.MARKET_TIMING, "timing explicite"),
    ("Combien vaut l'action Apple aujourd'hui ?", I.DONNEES_MARCHE, "donnée absente"),
    ("Quelle performance a réalisé mon ETF en août 2026 ?", I.DONNEES_MARCHE, "mesure historique indisponible"),
    ("Quel statut juridique pour facturer mes clients ?", I.HORS_SUJET, "professionnel"),
]
