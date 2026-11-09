"""Définit 21 messages fictifs et leurs intentions attendues.
Ce jeu de régression vérifie la classification, y compris les demandes ambiguës.
"""


from app.intents import Intent

# Chaque cas contient le message, l'intention attendue et une note de validation.
# Les cas « limite » couvrent les demandes pouvant relever de plusieurs intentions.

CAS: list[tuple[str, Intent, str]] = [
    # Allocation, cas nets
    ("J'ai 10000 € à placer sur 15 ans, plutôt prudent",
     Intent.ALLOCATION, "cas canonique"),
    ("Je viens de toucher une prime de 5000 €, qu'est-ce que j'en fais ?",
     Intent.ALLOCATION, "montant sans vocabulaire technique"),
    ("Je peux mettre 300 € par mois de côté, comment les placer ?",
     Intent.ALLOCATION, "versements réguliers"),
    ("J'aimerais préparer ma retraite, j'ai 40 ans et 50000 € d'épargne",
     Intent.ALLOCATION, "objectif long terme"),

    # Timing
    ("Les marchés sont au plus haut, je devrais attendre avant d'investir ?",
     Intent.MARKET_TIMING, "timing explicite"),
    ("Je vends mes actions maintenant ou j'attends la fin de l'année ?",
     Intent.MARKET_TIMING, "timing de sortie"),
    ("J'ai 20000 € à placer mais je me demande si c'est le bon moment",
     Intent.MARKET_TIMING, "LIMITE : allocation + timing, le timing doit gagner"),
    ("On est en fin de cycle non ? Vaut mieux rester liquide ?",
     Intent.MARKET_TIMING, "LIMITE : jargon, pas de verbe d'achat"),

    # Actif précis
    ("Je passe mes SOL en ETH, c'est plus solide non ?",
     Intent.ACTIF_PRECIS, "arbitrage entre deux tokens"),
    ("Ça vaut le coup d'acheter du Nvidia en ce moment ?",
     Intent.ACTIF_PRECIS, "LIMITE : contient aussi du timing"),
    ("Le S&P 500 ou le MSCI World pour mon PEA ?",
     Intent.ACTIF_PRECIS, "LIMITE : indices, pas titres individuels"),

    # Fiscalité
    ("PEA ou compte-titres pour investir en ETF ?",
     Intent.FISCALITE, "choix d'enveloppe"),
    ("Comment sont imposées les plus-values sur crypto en France ?",
     Intent.FISCALITE, "imposition directe"),
    ("Si je retire de mon PEA après 6 ans, je paie quoi ?",
     Intent.FISCALITE, "antériorité fiscale"),
    ("L'assurance-vie c'est intéressant fiscalement ?",
     Intent.FISCALITE, "LIMITE : pourrait passer pour de la pédagogie"),

    # Pédagogie
    ("C'est quoi la différence entre un ETF et un fonds classique ?",
     Intent.PEDAGOGIE, "définition"),
    ("Pourquoi on dit qu'il faut diversifier ?",
     Intent.PEDAGOGIE, "principe général"),
    ("Ça marche comment les intérêts composés ?",
     Intent.PEDAGOGIE, "mécanisme"),

    # Hors sujet
    ("Je devrais prendre un prêt sur 20 ou 25 ans pour mon appart ?",
     Intent.HORS_SUJET, "crédit immobilier"),
    ("Mon assurance auto a augmenté, je change ?",
     Intent.HORS_SUJET, "assurance"),
    ("Je dois créer une SASU ou une EURL ?",
     Intent.HORS_SUJET, "LIMITE : fiscalité, mais professionnelle"),
]
