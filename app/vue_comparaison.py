"""Affiche le formulaire SCF facultatif dans Streamlit et ses résultats.
Gère les saisies, le choix de comparaison et le téléchargement du graphique, sans appel LLM.
"""

from io import BytesIO
import streamlit as st
from pydantic import ValidationError
from . import comparaison_scf, clustering
from .models import Profil


@st.cache_data(show_spinner=False)
def echantillon_public():
    # Seules les données publiques sont mises en cache, jamais les montants saisis.
    return comparaison_scf.charger_echantillon()


CHAMPS = [
    ("age", "Votre âge (ans)", 18., 120., "Âge de la personne qui décrit la situation du foyer."),
    ("epargne_totale_eur", "Épargne et placements au total (€)", 0., None,
     "Comptes, livrets, assurance-vie, épargne retraite et placements. Sans votre logement."),
    ("actions_eur", "Dont actions et fonds en actions (€)", 0., None,
     "La part de cette épargne investie en actions, y compris via des ETF, fonds ou contrats. Mettez 0 si vous n'en détenez pas."),
    ("liquidites_eur", "Argent disponible sur comptes et livrets (€)", 0., None,
     "L'argent rapidement disponible, hors actions et placements bloqués."),
    ("revenu_mensuel_eur", "Revenus du foyer avant impôt (€/mois)", 0., None,
     "Tous les revenus du foyer avant impôt sur le revenu. Si vos revenus varient, utilisez une moyenne mensuelle habituelle."),
    ("patrimoine_total_eur", "Valeur totale de vos biens (€)", 0., None,
     "Épargne et placements + immobilier + autres biens (voiture, etc.). Ne déduisez pas les dettes."),
    ("dettes_eur", "Dettes restant à rembourser (€)", 0., None,
     "Le capital restant dû sur tous vos crédits. Mettez 0 si vous n'avez aucune dette."),
]


def afficher(profil: Profil):
    """Gère le choix de comparaison, la saisie locale et la validation des montants."""
    st.session_state.setdefault("scf_choix", None)
    st.session_state.setdefault("scf_resultat", None)
    with st.container(border=True):
        st.subheader("Et si vous vous compariez à d'autres ménages ?")
        st.write("Souhaitez-vous comparer votre situation à celle de ménages américains interrogés en 2022 ?")
        st.caption("Facultatif. Un repère pour comprendre votre situation, pas un objectif à atteindre ni un conseil d'investissement.")
        choix = st.session_state.scf_choix
        if choix is None:
            oui, non = st.columns(2)
            if oui.button("Oui, voir où je me situe", key="scf_oui", type="primary"):
                st.session_state.scf_choix = True
                st.rerun()
            if non.button("Pas maintenant", key="scf_non"):
                st.session_state.scf_choix = False
                st.rerun()
            return
        if choix is False:
            st.caption("Votre analyse reste disponible sans cette comparaison.")
            if st.button("Faire la comparaison", key="scf_reprendre"):
                st.session_state.scf_choix = True
                st.rerun()
            return

        st.write("Indiquez votre âge et les montants de votre foyer : épargne, actions, argent disponible, revenus, biens et dettes. Nous faisons les calculs pour vous.")
        st.caption("Utilisez le même périmètre partout : vous seul, ou vous et votre conjoint. Les montants restent dans cette session et ne sont pas envoyés au modèle de langage par ce formulaire.")
        with st.expander("Vos informations pour la comparaison", expanded=st.session_state.scf_resultat is None):
            with st.form("comparaison_scf_form"):
                valeurs = {}
                for nom, label, minimum, maximum, aide in CHAMPS:
                    valeurs[nom] = st.number_input(label, min_value=minimum, max_value=maximum,
                        value=None, step=1. if nom == "age" else 100., help=aide, key="scf_" + nom)
                    if nom == "liquidites_eur":
                        st.caption("Exemple : 6 000 € disponibles et 2 000 € de revenu mensuel = 3 mois de revenu. Saisissez les euros, nous calculons les mois.")
                    if nom == "dettes_eur":
                        st.caption("Indiquez ce qu'il reste à rembourser, pas vos mensualités.")
                if st.form_submit_button("Afficher ma comparaison", type="primary"):
                    # Invalider l'ancien résultat immédiatement : une saisie
                    # erronée ne doit jamais laisser croire à un résultat actualisé.
                    st.session_state.scf_resultat = None
                    manquants = [label for nom, label, *_ in CHAMPS if valeurs[nom] is None]
                    if manquants:
                        st.warning("À compléter : " + ", ".join(manquants) + ".")
                    elif any(valeurs[c] == 0 for c in ("epargne_totale_eur", "revenu_mensuel_eur", "patrimoine_total_eur")):
                        st.warning("Cette comparaison nécessite une épargne, un revenu habituel et une valeur de biens supérieurs à zéro. Sinon, certains rapports ne peuvent pas être calculés ; vous pouvez ignorer cette étape.")
                    else:
                        try:
                            saisie = comparaison_scf.MontantsComparaison(**valeurs)
                            compare = saisie.vers_profil(profil)
                            modele = clustering.comparer(compare)
                            st.session_state.scf_resultat = {"profil": compare.model_dump(), "modele": modele.to_dict()}
                            st.rerun()
                        except ValidationError as erreur:
                            st.error(erreur.errors()[0]["msg"].removeprefix("Value error, "))

        resultat = st.session_state.scf_resultat
        if resultat:
            _afficher_resultat(resultat)
        if st.button("Masquer la comparaison", key="scf_masquer"):
            st.session_state.scf_choix = False
            st.session_state.scf_resultat = None
            st.rerun()


def _afficher_resultat(resultat):
    """Affiche les distributions, le résultat du modèle et les détails méthodologiques."""
    profil = Profil.model_validate(resultat["profil"])
    try:
        echantillon = echantillon_public()
        lignes = comparaison_scf.positions(profil, echantillon)
        fig = comparaison_scf.graphique(profil, echantillon)
    except (OSError, ValueError, KeyError, ImportError):
        st.warning("Les données de l'enquête ne sont pas disponibles. Le graphique ne peut pas être affiché pour le moment ; vos saisies sont conservées.")
        return
    st.subheader("Votre position, en un coup d'œil")
    st.write("Le trait orange vous représente. Le pointillé vert indique la médiane : la moitié des ménages se trouve de chaque côté.")
    st.pyplot(fig, width="stretch")
    st.caption(f"Source : enquête américaine SCF 2022 · {len(echantillon):,} ménages avec données exploitables · échantillon non pondéré. Plus à droite signifie une valeur plus élevée, pas une meilleure situation.".replace(",", " "))
    # Rang sur les valeurs brutes : ne pas confondre une barre regroupée à
    # droite avec un plafonnement des données servant à cette comparaison.
    part = lignes[1]
    st.write(f"Votre part d'épargne en actions est de **{part['vous']:.1f} %**. Dans cet échantillon, **{part['part_inferieure_ou_egale']:.0f} %** des ménages en détiennent une part inférieure ou égale.")
    st.caption("Les revenus, systèmes de retraite et habitudes d'épargne diffèrent entre pays. Cette comparaison ne classe pas les ménages du meilleur au moins bon.")
    modele = resultat["modele"]
    if modele["statut"] == "utilise":
        moy = modele["moyennes_segment"]
        st.write(f"**Le groupe qui vous ressemble le plus** détient en moyenne **{moy['part_risquee']*100:.1f} %** de son épargne en actions et dispose de **{moy['coussin_mois']:.1f} mois de revenu** en argent disponible. Ce sont des observations, pas des montants à viser.")
    elif modele["statut"] == "hors_distribution":
        st.info("Votre situation est trop différente des groupes repérés par le modèle pour vous associer à l'un d'eux. Le graphique permet quand même de vous situer dans l'échantillon.")
    else:
        st.info("Le regroupement automatique n'est pas disponible. Le graphique reste une comparaison descriptive avec l'échantillon.")
    image = BytesIO()
    fig.savefig(image, format="png", dpi=150, bbox_inches="tight")
    st.download_button("Enregistrer le graphique", image.getvalue(), file_name="ma_comparaison_scf.png", mime="image/png", key="scf_graphique")
    with st.expander("Comment lire cette comparaison ?"):
        st.write("Une barre plus haute contient davantage de ménages. La dernière barre de chaque graphique rassemble les valeurs égales ou supérieures à sa borne, marquée « + ». Votre repère n'est jamais tronqué. Les médianes et positions sont calculées sur les valeurs non plafonnées.")
        st.write("Les montants ne sont pas comparés entre euros et dollars : nous utilisons des proportions et des mois de revenu. Le regroupement automatique utilise les mêmes ratios, plafonnés comme lors de son entraînement ; ses moyennes portent sur ces valeurs plafonnées.")
        st.caption("Premier implicat de l'enquête ; ménages avec ratios calculables, sans pondération d'enquête. Ces pourcentages décrivent l'échantillon retenu, pas l'ensemble de la population américaine.")
        st.markdown("[Consulter la source : Federal Reserve, SCF 2022](https://www.federalreserve.gov/econres/scfindex.htm)")
    with st.expander("Détails du calcul et du modèle"):
        st.json({"ratios_calcules": {c: getattr(profil,c) for c in clustering.CHAMPS}, "modele": modele})
