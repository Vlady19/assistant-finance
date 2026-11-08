"""
evals/cas.py — le jeu de test.

=============================================================================
 UNE ÉVAL, C'EST QUOI ?
=============================================================================

Une liste de cas avec la réponse attendue, et un script qui compte les
réussites. C'est tout. Pas de bibliothèque, pas de plateforme.

Ce fichier est le plus important du projet, et c'est le moins impressionnant.

POURQUOI IL CHANGE TOUT
  Sans lui, quand tu modifies un prompt, tu testes trois messages à la main,
  ça a l'air mieux, tu gardes. Tu ne sauras jamais que ta modification a
  cassé six autres cas.

  Avec lui, tu as un chiffre. « 17/20 avant, 19/20 après » : tu sais.

LA RÈGLE D'OR
  Chaque fois qu'un cas réel échoue en production, tu l'ajoutes ici. Le jeu
  grandit avec les erreurs rencontrées, et une régression déjà corrigée ne
  peut plus revenir sans que tu le voies.

CE QUE CE FICHIER NE FAIT PAS
  Il ne teste que la classification d'intentions. C'est le composant le plus
  facile à évaluer : une seule bonne réponse par cas.

  Évaluer l'extraction de profil se fait exactement pareil (message attendu
  -> profil attendu, on compare champ par champ). Évaluer la rédaction est
  bien plus difficile, parce qu'il n'y a pas UNE bonne réponse — on y revient
  plus tard.
"""

from app.intents import Intent

# Chaque cas : (message, intention attendue, note pour toi)
#
# Les cas marqués « limite » sont ceux où un humain pourrait hésiter. Garde-les :
# ce sont eux qui te disent où ton système est fragile. Un jeu de test composé
# uniquement de cas évidents affiche 100 % et ne t'apprend rien.

CAS: list[tuple[str, Intent, str]] = [
    # ── Allocation, cas nets ──────────────────────────────────────────────
    ("J'ai 10000 € à placer sur 15 ans, plutôt prudent",
     Intent.ALLOCATION, "cas canonique"),
    ("Je viens de toucher une prime de 5000 €, qu'est-ce que j'en fais ?",
     Intent.ALLOCATION, "montant sans vocabulaire technique"),
    ("Je peux mettre 300 € par mois de côté, comment les placer ?",
     Intent.ALLOCATION, "versements réguliers"),
    ("J'aimerais préparer ma retraite, j'ai 40 ans et 50000 € d'épargne",
     Intent.ALLOCATION, "objectif long terme"),

    # ── Timing ────────────────────────────────────────────────────────────
    ("Les marchés sont au plus haut, je devrais attendre avant d'investir ?",
     Intent.MARKET_TIMING, "timing explicite"),
    ("Je vends mes actions maintenant ou j'attends la fin de l'année ?",
     Intent.MARKET_TIMING, "timing de sortie"),
    ("J'ai 20000 € à placer mais je me demande si c'est le bon moment",
     Intent.MARKET_TIMING, "LIMITE : allocation + timing, le timing doit gagner"),
    ("On est en fin de cycle non ? Vaut mieux rester liquide ?",
     Intent.MARKET_TIMING, "LIMITE : jargon, pas de verbe d'achat"),

    # ── Actif précis ──────────────────────────────────────────────────────
    ("Je passe mes SOL en ETH, c'est plus solide non ?",
     Intent.ACTIF_PRECIS, "arbitrage entre deux tokens"),
    ("Ça vaut le coup d'acheter du Nvidia en ce moment ?",
     Intent.ACTIF_PRECIS, "LIMITE : contient aussi du timing"),
    ("Le S&P 500 ou le MSCI World pour mon PEA ?",
     Intent.ACTIF_PRECIS, "LIMITE : indices, pas titres individuels"),

    # ── Fiscalité ─────────────────────────────────────────────────────────
    ("PEA ou compte-titres pour investir en ETF ?",
     Intent.FISCALITE, "choix d'enveloppe"),
    ("Comment sont imposées les plus-values sur crypto en France ?",
     Intent.FISCALITE, "imposition directe"),
    ("Si je retire de mon PEA après 6 ans, je paie quoi ?",
     Intent.FISCALITE, "antériorité fiscale"),
    ("L'assurance-vie c'est intéressant fiscalement ?",
     Intent.FISCALITE, "LIMITE : pourrait passer pour de la pédagogie"),

    # ── Pédagogie ─────────────────────────────────────────────────────────
    ("C'est quoi la différence entre un ETF et un fonds classique ?",
     Intent.PEDAGOGIE, "définition"),
    ("Pourquoi on dit qu'il faut diversifier ?",
     Intent.PEDAGOGIE, "principe général"),
    ("Ça marche comment les intérêts composés ?",
     Intent.PEDAGOGIE, "mécanisme"),

    # ── Hors sujet ────────────────────────────────────────────────────────
    ("Je devrais prendre un prêt sur 20 ou 25 ans pour mon appart ?",
     Intent.HORS_SUJET, "crédit immobilier"),
    ("Mon assurance auto a augmenté, je change ?",
     Intent.HORS_SUJET, "assurance"),
    ("Je dois créer une SASU ou une EURL ?",
     Intent.HORS_SUJET, "LIMITE : fiscalité, mais professionnelle"),
]
