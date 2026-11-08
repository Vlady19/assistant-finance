"""Interface V6 : collecte, conversation et preuves de calcul conservées en session."""
import inspect
from dataclasses import asdict
import streamlit as st
from pydantic import ValidationError
from app import conversation, pipeline, vue_comparaison
from app.models import Profil

st.set_page_config(page_title="Assistant finance", page_icon="📊", layout="wide")
if "profil" not in st.session_state:
    st.session_state.profil = conversation.profil_vide()
    st.session_state.messages = []
    st.session_state.derniere_question = None


def memoriser(reponse):
    st.session_state.profil = reponse.profil
    st.session_state.derniere_question = reponse.derniere_question
    st.session_state.messages.append({"role": "assistant", "reponse": asdict(reponse)})
    if reponse.termine:
        # Après une nouvelle analyse, proposer à nouveau la comparaison.
        st.session_state.scf_choix = None
        st.session_state.scf_resultat = None


def afficher(message):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["texte"])
            return
        r = message["reponse"]
        st.markdown(r["texte"])
        if r["dossier"]:
            # Les anciennes sessions peuvent contenir le dossier SCF V6.
            # Reconstruire l'affichage depuis la trace masque aussi cet ancien
            # bloc automatique, sans effacer les messages de l'utilisateur.
            dossier = (pipeline.dossier_depuis_trace(r["trace"], inclure_comparaison=False)
                       if r["trace"].get("allocation_illustrative") is not None else r["dossier"])
            st.markdown(dossier.replace("Résultats calculés par Python", "Votre situation"))
        if r["repli_utilise"]:
            st.caption("Réponse de secours utilisée ; aucun résultat manquant n'a été inventé.")
        if r["trace"]:
            with st.expander("Vérifier les données et les calculs"):
                st.json(r["trace"])
                if r["trace"].get("outil"):
                    st.caption("Fonction Python effectivement appelée, avec entrées et résultats ci-dessus.")
                    st.code(inspect.getsource(pipeline.calculer), language="python")
        if r["problemes_validation"]:
            with st.expander("Contrôles de la rédaction"):
                st.write(r["problemes_validation"])


with st.sidebar:
    st.subheader("Profil en cours")
    p = st.session_state.profil
    essentiels = conversation.ORDRE_DES_QUESTIONS
    st.progress(sum(getattr(p, c) is not None for c in essentiels) / len(essentiels))
    libelles = {"montant_eur":"Capital à étudier", "horizon_annees":"Horizon",
                "tolerance_risque":"Tolérance au risque", "epargne_precaution_mois":"Épargne de précaution",
                "resident_francais":"Résidence fiscale française"}
    for champ, libelle in libelles.items():
        valeur = getattr(p, champ)
        if valeur is None:
            affiche = "non renseigné"
        elif champ == "montant_eur":
            affiche = pipeline._euros(valeur)
        elif champ == "horizon_annees":
            affiche = f"{valeur:g} ans"
        elif champ == "epargne_precaution_mois":
            affiche = f"{valeur:g} mois de dépenses"
        elif champ == "resident_francais":
            affiche = "Oui" if valeur else "Non"
        else:
            affiche = {"prudent":"Prudente", "equilibre":"Équilibrée", "dynamique":"Dynamique"}[valeur]
        st.caption(f"{libelle} : {affiche}")
    if st.button("Recommencer"):
        st.session_state.clear()
        st.rerun()

st.title("Assistant finance")
st.caption("Comprendre son épargne et explorer une situation. Ces éléments ne constituent pas un conseil en investissement.")
st.caption("Pas de cours de marché en direct.")

with st.expander("Renseigner ou corriger ma situation"):
    st.write("Ces informations servent à illustrer une répartition de votre épargne. La comparaison avec d’autres ménages vous sera proposée ensuite, si vous le souhaitez.")
    with st.form("profil_form"):
        capital = st.number_input("Capital à étudier (€)", min_value=0.00, value=p.montant_eur, step=100.0)
        horizon = st.number_input("Horizon (années)", min_value=0.01, value=p.horizon_annees, step=1.0)
        reserve = st.number_input("Épargne disponible (mois de dépenses)", min_value=0.0, value=p.epargne_precaution_mois, step=1.0)
        niveaux = ["Non renseigné", "prudent", "equilibre", "dynamique"]
        risque = st.selectbox("Tolérance au risque", niveaux, index=niveaux.index(p.tolerance_risque) if p.tolerance_risque else 0)
        residence = st.selectbox("Résidence fiscale française", ["Non renseignée", "Oui", "Non"], index=0 if p.resident_francais is None else (1 if p.resident_francais else 2))
        if st.form_submit_button("Analyser mon épargne"):
            try:
                donnees = p.model_dump()
                donnees.update(montant_eur=capital, horizon_annees=horizon,
                    tolerance_risque=None if risque == niveaux[0] else risque,
                    epargne_precaution_mois=reserve,
                    resident_francais={"Non renseignée":None,"Oui":True,"Non":False}[residence])
                nouveau = Profil.model_validate(donnees)
                if not conversation.est_complet(nouveau):
                    st.warning("Complétez ces cinq informations avant l’analyse.")
                else:
                    memoriser(pipeline.analyser_profil(nouveau, inclure_comparaison=False))
                    st.rerun()
            except ValidationError:
                st.error("Une valeur est invalide. Vérifiez le formulaire.")

for message in st.session_state.messages:
    afficher(message)
if not st.session_state.messages:
    st.write("Posez une question sur l'épargne ou décrivez votre capital, votre horizon et votre tolérance au risque. Vous pouvez aussi utiliser le formulaire de calcul local.")

# La comparaison apparaît après une analyse, jamais comme un formulaire
# supplémentaire obligatoire ni comme un résultat obtenu sans demande.
if conversation.est_complet(st.session_state.profil) and any(
    m.get("reponse", {}).get("termine") for m in st.session_state.messages
):
    vue_comparaison.afficher(st.session_state.profil)

if message := st.chat_input("Votre message"):
    st.session_state.messages.append({"role":"user", "texte":message})
    with st.spinner("Analyse de la demande…"):
        reponse = pipeline.traiter(message, st.session_state.profil, st.session_state.derniere_question, inclure_comparaison=False)
    memoriser(reponse)
    st.rerun()
