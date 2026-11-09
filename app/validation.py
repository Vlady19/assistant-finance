"""Contrôle la rédaction : nombres, garanties, prédictions et mention informative.
Fournit le texte de secours ; ces contrôles lexicaux ne vérifient pas tous les faits.
"""

import re
import unicodedata
from dataclasses import dataclass, field

MENTION = "Ces éléments sont informatifs et ne constituent pas un conseil en investissement."

@dataclass
class Resultat:
    valide: bool
    problemes: list[str] = field(default_factory=list)
    def resume(self):
        return "; ".join(self.problemes)

def _normaliser(texte):
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower())
                   if unicodedata.category(c) != "Mn")

def valider(reponse: str, dossier: str = "") -> Resultat:
    # Le dossier n'autorise pas à réemployer un montant comme un rendement.
    # Aucun chiffre n'est confié à la prose libre, même s'il existe dans le dossier.
    """Détecte les nombres et formulations interdites, puis vérifie la mention informative."""
    if not isinstance(reponse, str) or not reponse.strip():
        return Resultat(False, ["réponse vide"])
    texte = _normaliser(reponse)
    problemes = []
    if re.search(r"\d|%|€|pour\s*cent|\b(deux|trois|quatre|cinq|six|sept|huit|neuf|dix|vingt|trente|cent|mille|million)s?\b", texte):
        problemes.append("chiffres interdits dans l'explication : affichage réservé à Python")
    motifs = [
        r"\b(je|nous)\s+(vous\s+)?(recommande|recommandons|conseille|conseillons)\b",
        r"\bvous\s+(devez|devriez)\s+(acheter|vendre|investir)\b",
        r"\b(va monter|va baisser|vous gagnerez|rapportera)\b",
    ]
    if any(re.search(m, texte) for m in motifs):
        problemes.append("injonction ou prédiction non autorisée")
    # Accepter les négations usuelles, sans supprimer le contrôle de garantie.
    sans_negations = re.sub(r"aucun\s+(rendement|gain)\s+n['’]est\s+garanti", "", texte)
    sans_negations = re.sub(r"n['’]est\s+(pas|jamais)\s+(garanti|sans risque)", "", sans_negations)
    if re.search(r"\b(garanti[e]?s?|sans risque|risque zero)\b", sans_negations):
        problemes.append("formulation de garantie ambiguë")
    if not re.search(r"ne constituent? pas un conseil", texte):
        problemes.append("mention informative absente")
    return Resultat(not problemes, problemes)

def rendu_de_secours(dossier: str) -> str:
    """Fournit un texte fixe lorsque l'explication ne peut pas être validée."""
    if not dossier or dossier == "(sans objet)":
        return "Je ne peux pas fournir une explication vérifiée pour cette demande. Reformulez votre question. " + MENTION
    return "Les résultats calculés sont présentés ci-dessous. L'explication automatique est indisponible. " + MENTION
