"""Orchestration V6 : langage → profil → calculs Python → explication contrôlée.

Les fonctions métier restent indépendantes de l'interface et du fournisseur.
La trace expose des entrées et résultats vérifiables, pas un raisonnement caché.
"""
from dataclasses import dataclass, field
import json
from openai import OpenAIError
from pydantic import ValidationError
from . import conversation, intents, redaction, regles, validation, clustering
from .llm import extraire_profil
from .models import QUESTIONS, Profil
from .config import ServiceIndisponible

@dataclass
class Reponse:
    texte: str
    profil: Profil
    derniere_question: str | None
    intent: intents.Intent
    politique: intents.Politique
    termine: bool = False
    problemes_validation: list[str] | None = None
    repli_utilise: bool = False
    dossier: str = ""
    trace: dict = field(default_factory=dict)


def traiter(message: str, profil: Profil, derniere_question: str | None = None, *, inclure_comparaison: bool = True) -> Reponse:
    if not message.strip() or len(message) > 12000:
        return Reponse("Écrivez une demande non vide, de longueur raisonnable.", profil,
                       derniere_question, intents.Intent.PEDAGOGIE, intents.Politique.EXPLIQUER)
    try:
        # Le contexte aide à comprendre « oui », SANS enfermer toute nouvelle
        # question dans la collecte d'un profil.
        classification = intents.classer(message, derniere_question=derniere_question)
        intent = classification.intent
        politique = intents.politique_de(intent)
        if politique is intents.Politique.ANALYSER:
            return _analyser(message, profil, derniere_question, intent, politique, inclure_comparaison)
        if intent is intents.Intent.DONNEES_MARCHE:
            texte = ("Je n'ai pas de source de cours ou de performances de marché connectée. "
                     "Je ne peux donc pas donner ou vérifier cette valeur. " + validation.MENTION)
            return Reponse(texte, profil, derniere_question, intent, politique,
                           trace={"source_marche": "indisponible", "classification": intent.value})
        if politique is intents.Politique.REFUSER:
            return Reponse("Cette demande sort du périmètre de cet assistant consacré au placement de l'épargne. "
                           "Vous pouvez me poser une question sur la diversification ou décrire votre épargne. "
                           + validation.MENTION, profil, derniere_question, intent, politique)
        texte, problemes, repli = _rediger_et_valider(politique, "", message)
        return Reponse(texte, profil, derniere_question, intent, politique,
                       problemes_validation=problemes, repli_utilise=repli,
                       trace={"classification": intent.value, "source": "connaissances générales du LLM, sans données de marché"})
    except ValidationError:
        return Reponse("Une valeur du profil est invalide. Vérifiez les montants et durées positifs, "
                       "les ratios et l'âge ; aucune mise à jour n'a été enregistrée.", profil,
                       derniere_question, intents.Intent.ALLOCATION, intents.Politique.ANALYSER,
                       trace={"erreur": "profil_invalide"})
    except (OpenAIError, ServiceIndisponible) as erreur:
        texte = str(erreur) if isinstance(erreur, ServiceIndisponible) else (
            "Le service de compréhension est indisponible. Votre profil est conservé ; réessayez dans un instant.")
        return Reponse(texte, profil, derniere_question, intents.Intent.PEDAGOGIE,
                       intents.Politique.EXPLIQUER, repli_utilise=True,
                       trace={"erreur": type(erreur).__name__})


def _rediger_et_valider(politique, dossier, message):
    problemes = []
    for _ in range(2):
        correction = message if not problemes else message + "\nContrôle précédent : " + "; ".join(problemes)
        try:
            texte = redaction.rediger(politique, dossier=dossier, message=correction)
        except (OpenAIError, ServiceIndisponible):
            return validation.rendu_de_secours(dossier), ["service de rédaction indisponible"], True
        resultat = validation.valider(texte, dossier)
        if resultat.valide:
            return texte, problemes or None, False
        problemes = resultat.problemes
    return validation.rendu_de_secours(dossier), problemes, True


def _analyser(message, profil, derniere_question, intent, politique, inclure_comparaison):
    nouveau = extraire_profil(message, conversation.resume_lisible(profil), derniere_question)
    profil = conversation.fusionner(profil, nouveau)
    if profil.montant_eur == 0:
        return Reponse(
        "Vous m'indiquez ne pas avoir de capital à investir pour le moment. "
        "Il n'y a donc pas d'allocation à calculer.",
        profil,
        None,
        intent,
        politique,
        termine=True
    )
    
    if profil.montant_eur is not None and 0 < profil.montant_eur < 1:
        return Reponse(
        "Le montant indiqué est inférieur à 1 €. "
        "Il est trop faible pour produire une illustration d'allocation pertinente.",
        profil,
        None,
        intent,
        politique,
        termine=True
    )

    champ = conversation.prochain_champ_manquant(profil)
    if champ:
        return Reponse(QUESTIONS[champ], profil, QUESTIONS[champ], intent, politique)
    return analyser_profil(profil, message=message, avec_llm=True, inclure_comparaison=inclure_comparaison)


def _euros(montant):
    return f"{montant:,.2f} €".replace(",", " ").replace(".", ",")


def calculer(profil: Profil, *, inclure_comparaison: bool = True) -> dict:
    """Outil Python typé, borné et testable. Pas de code généré ni d'appel réseau."""
    if not conversation.est_complet(profil):
        raise ValueError("Profil incomplet : collecte nécessaire avant les calculs.")
    niveau = regles.niveau_retenu(profil)
    lignes = []
    if regles.allocation_autorisee(profil):
        for libelle, pourcentage in regles.repartition(niveau).items():
            lignes.append({"classe": libelle, "pourcentage": pourcentage,
                           "montant_eur": round(profil.montant_eur * pourcentage / 100, 2)})
        # Garantir la somme au centime après arrondi de chaque ligne.
        lignes[-1]["montant_eur"] = round(round(profil.montant_eur, 2) - sum(x["montant_eur"] for x in lignes[:-1]), 2)
    return {"outil": "app.pipeline.calculer", "entrees": profil.model_dump(),
            "niveau_regles": regles.NIVEAUX[niveau], "allocation_illustrative": lignes,
            "allocation_suspendue": not lignes, "alertes": regles.alertes(profil),
            "clustering": (clustering.comparer(profil).to_dict() if inclure_comparaison else
                {"statut": "non_demandee", "explication": "Comparaison facultative non demandée.", "avertissements": []}),
            "sources": {"profil": "déclarations utilisateur", "allocation": "règles pédagogiques explicites de app/regles.py",
                        "segmentation": "Federal Reserve, SCF 2022, premier implicat"}}


def dossier_depuis_trace(trace: dict, *, inclure_comparaison: bool = True) -> str:
    profil = trace["entrees"]
    lignes = ["**Résultats calculés par Python**",
              f"Capital déclaré : {_euros(profil['montant_eur'])}. Horizon : {profil['horizon_annees']:g} ans.",
              f"Précaution : {profil['epargne_precaution_mois']:g} mois de dépenses.",
              f"Niveau retenu par les règles : {trace['niveau_regles']}."]
    if trace["allocation_suspendue"]:
        lignes.append("Illustration d'allocation suspendue : horizon trop court ou épargne de précaution insuffisante selon les règles du projet.")
    else:
        lignes += ["Illustration pédagogique issue de règles fixes, pas d'une optimisation financière :"]
        for ligne in trace["allocation_illustrative"]:
            lignes.append(f"- {ligne['classe']} : {ligne['pourcentage']} % — {_euros(ligne['montant_eur'])}")
    lignes += ["\n" + a for a in trace["alertes"]]
    if not inclure_comparaison or trace["clustering"]["statut"] == "non_demandee":
        return "\n\n".join(lignes)
    ml = trace["clustering"]
    lignes += ["\n**Comparaison aux ménages SCF**", ml["explication"]]
    if ml["statut"] == "utilise":
        m = ml["moyennes_segment"]
        lignes += [f"Segment {ml['cluster']} ; distance standardisée : {ml['distance']:.3f} (ce n'est pas une probabilité).",
                   f"Moyennes du segment après plafonnement : âge {m['age']:.1f} ans ; actions {m['part_risquee']*100:.1f} % ; "
                   f"liquidités {m['coussin_mois']:.1f} mois de revenu ; dette/actifs {m['levier']:.1%}."]
    lignes += ml["avertissements"]
    lignes += ["Aucun prix, rendement attendu ou indicateur de marché n'a été calculé."]
    return "\n\n".join(lignes)


def _construire_dossier(profil):
    return dossier_depuis_trace(calculer(profil))


def analyser_profil(profil: Profil, message: str = "Expliquer le résultat", avec_llm: bool = False, *, inclure_comparaison: bool = True) -> Reponse:
    """Même outil pour le chat et le formulaire local, donc mêmes contrôles."""
    if profil.montant_eur == 0:
        return Reponse(
            "Vous n'avez actuellement aucun capital à investir. "
            "Il n'y a donc pas d'allocation à calculer.",
            profil,
            None,
            intents.Intent.ALLOCATION,
            intents.Politique.ANALYSER,
            termine=True,
        )
    if 0 < profil.montant_eur < 1:
        return Reponse(
            "Le montant indiqué est inférieur à 1 €. "
            "Il est trop faible pour produire une illustration d'allocation pertinente.",
            profil,
            None,
            intents.Intent.ALLOCATION,
            intents.Politique.ANALYSER,
            termine=True
        )
    trace = calculer(profil, inclure_comparaison=inclure_comparaison)
    dossier = dossier_depuis_trace(trace)
    if avec_llm:
        # Le rédacteur des règles n'a pas accès aux observations SCF ni au
        # message brut : il ne peut pas les citer comme causes de l'allocation.
        faits_regles = {"capital": profil.montant_eur, "horizon": profil.horizon_annees,
            "precaution_mois_depenses": profil.epargne_precaution_mois,
            "tolerance_declaree": profil.tolerance_risque,
            "capacite": regles.NIVEAUX[regles.capacite_risque(profil)],
            "niveau_retenu": trace["niveau_regles"],
            "allocation_suspendue": trace["allocation_suspendue"],
            "methode": "Le minimum entre tolérance et capacité. La capacité dépend uniquement de l'horizon et de la précaution."}
        texte, problemes, repli = _rediger_et_valider(intents.Politique.ANALYSER,
            json.dumps(faits_regles, ensure_ascii=False), "Expliquer les règles et leurs limites, sans ajouter de cause.")
    else:
        texte, problemes, repli = "Calcul local effectué. " + validation.MENTION, None, False
    return Reponse(texte, profil, None, intents.Intent.ALLOCATION, intents.Politique.ANALYSER,
                   True, problemes, repli, dossier, trace)
