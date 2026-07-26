# ============================================================
# CMA URGENCE ENTREPRISES
# Version 1.2 - Streamlit
# Navigation corrigée + guides courriers + statistiques entreprises + exports journaliers
# ============================================================

from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Any

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CMA Urgence Entreprises",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "CMA Urgence Entreprises"
CMA_RED = "#D71920"
CMA_RED_DARK = "#A20F18"
TEXT_DARK = "#172033"
TEXT_MUTED = "#667085"
BACKGROUND = "#F4F6F8"
CARD_BACKGROUND = "#FFFFFF"
BORDER_COLOR = "#E3E7ED"

STATUS_COLORS = {
    "Critique": [215, 25, 32, 225],
    "À rappeler": [241, 145, 0, 225],
    "Accompagnement en cours": [38, 113, 221, 225],
    "Activité reprise": [22, 163, 74, 225],
    "Clôturé": [102, 112, 133, 225],
}

STATUS_HEX = {
    "Critique": "#D71920",
    "À rappeler": "#F19100",
    "Accompagnement en cours": "#2671DD",
    "Activité reprise": "#16A34A",
    "Clôturé": "#667085",
}

URGENCY_LEVELS = ["Faible", "Modérée", "Élevée", "Critique"]

COMMUNES_COORDONNEES = {
    "Le Porge": (44.8729, -1.0926),
    "Lacanau": (44.9772, -1.0767),
    "Saumos": (44.9028, -0.9928),
    "Lège-Cap-Ferret": (44.7935, -1.1460),
    "Sainte-Hélène": (44.9665, -0.8841),
    "Carcans": (45.0786, -1.0447),
    "Hourtin": (45.1867, -1.0563),
    "Castelnau-de-Médoc": (45.0278, -0.8009),
    "Saint-Jean-d’Illac": (44.8082, -0.7832),
    "Salaunes": (44.9367, -0.8309),
    "Bordeaux": (44.8378, -0.5792),
}

IMPORT_COLUMNS = [
    "SIREN",
    "Raison sociale",
    "Commune",
    "Téléphone",
    "Email",
    "Activité",
    "Conseiller",
    "Date de rappel",
]


ORGANISM_GUIDES = {
    "Assurance": {
        "recipient": "Service sinistres de la compagnie d’assurance",
        "subject": "Déclaration de sinistre et demande d’ouverture du dossier",
        "request": (
            "Nous sollicitons l’ouverture du dossier de sinistre, la confirmation "
            "des garanties mobilisables et l’organisation rapide d’une expertise."
        ),
        "tasks": [
            "Sécuriser les locaux et éviter l’aggravation des dommages.",
            "Déclarer le sinistre dans le délai prévu au contrat.",
            "Demander un numéro de dossier et les coordonnées du gestionnaire.",
            "Ne pas jeter les biens endommagés avant accord ou expertise.",
            "Chiffrer les pertes matérielles et l’interruption d’activité.",
            "Conserver la preuve de tous les échanges et dépenses d’urgence.",
        ],
        "documents": [
            "Contrat et attestation d’assurance.",
            "Photos et vidéos datées des dommages.",
            "Inventaire des biens endommagés avec factures disponibles.",
            "Dépôt de plainte ou constat des autorités, si applicable.",
            "Devis de remise en état et factures des mesures conservatoires.",
            "Éléments comptables utiles à la perte d’exploitation.",
            "RIB de l’entreprise.",
        ],
    },
    "Banque": {
        "recipient": "Direction de l’agence bancaire",
        "subject": "Demande de soutien temporaire liée à une situation de crise",
        "request": (
            "Nous sollicitons un rendez-vous rapide afin d’étudier les solutions "
            "temporaires de trésorerie, de report d’échéances ou d’aménagement des concours bancaires."
        ),
        "tasks": [
            "Actualiser le besoin de trésorerie à 30, 60 et 90 jours.",
            "Lister les échéances bancaires et charges prioritaires.",
            "Prendre contact avec le conseiller professionnel.",
            "Demander par écrit les solutions et leurs coûts.",
            "Vérifier les garanties et assurances liées aux prêts.",
        ],
        "documents": [
            "Derniers comptes annuels ou liasse fiscale.",
            "Situation comptable récente.",
            "Plan de trésorerie prévisionnel.",
            "Relevés bancaires récents.",
            "Tableau des emprunts et échéances.",
            "Justificatifs de sinistre ou de fermeture.",
            "RIB et pièce d’identité du dirigeant si demandés.",
        ],
    },
    "URSSAF": {
        "recipient": "Service des entreprises en difficulté de l’URSSAF",
        "subject": "Demande de délai de paiement des cotisations sociales",
        "request": (
            "Nous sollicitons l’étude d’un délai ou d’un échéancier adapté, "
            "compte tenu des conséquences immédiates de la crise sur l’activité et la trésorerie."
        ),
        "tasks": [
            "Vérifier les échéances sociales dues et à venir.",
            "Déposer les déclarations même en cas de difficulté de paiement.",
            "Formuler la demande depuis l’espace en ligne de l’entreprise.",
            "Proposer un échéancier réaliste et documenté.",
            "Conserver l’accusé de réception et suivre la réponse.",
        ],
        "documents": [
            "SIREN et coordonnées de l’entreprise.",
            "Montant et nature des échéances concernées.",
            "Situation de trésorerie et plan prévisionnel.",
            "Justificatifs de la baisse ou de l’arrêt d’activité.",
            "Relevés bancaires récents si demandés.",
            "Proposition d’échéancier.",
        ],
    },
    "DGFIP": {
        "recipient": "Service des impôts des entreprises",
        "subject": "Demande de délai ou de mesure adaptée pour les échéances fiscales",
        "request": (
            "Nous sollicitons l’examen d’un délai de paiement ou de toute mesure "
            "adaptée à la situation exceptionnelle rencontrée par l’entreprise."
        ),
        "tasks": [
            "Identifier précisément les impôts et échéances concernés.",
            "Maintenir les déclarations fiscales dans les délais.",
            "Contacter le service des impôts des entreprises.",
            "Présenter une demande motivée, chiffrée et temporaire.",
            "Suivre la messagerie sécurisée de l’espace professionnel.",
        ],
        "documents": [
            "Avis ou références des échéances fiscales concernées.",
            "Situation de trésorerie.",
            "Derniers comptes ou situation comptable.",
            "Justificatifs du sinistre et de ses conséquences.",
            "Plan de règlement proposé.",
            "Coordonnées de l’expert-comptable, le cas échéant.",
        ],
    },
    "Activité partielle / DDETS": {
        "recipient": "Service compétent en matière d’activité partielle",
        "subject": "Demande d’accompagnement pour la mise en place de l’activité partielle",
        "request": (
            "Nous sollicitons l’examen de la situation de l’entreprise et un accompagnement "
            "pour mobiliser le dispositif d’activité partielle lorsque les conditions sont réunies."
        ),
        "tasks": [
            "Évaluer les salariés et heures potentiellement concernés.",
            "Consulter le CSE lorsqu’il existe et selon les règles applicables.",
            "Informer les salariés de la démarche.",
            "Créer ou vérifier l’accès au portail dédié.",
            "Déposer la demande avec un motif précis et des justificatifs.",
            "Suivre la décision et effectuer les demandes d’indemnisation.",
        ],
        "documents": [
            "SIRET de l’établissement.",
            "Liste des salariés et durée du travail.",
            "Période et volume d’heures envisagés.",
            "Description circonstanciée de l’événement.",
            "Justificatifs de fermeture, d’inaccessibilité ou de baisse d’activité.",
            "Avis du CSE lorsqu’il est requis.",
            "RIB de l’établissement.",
        ],
    },
    "Bailleur": {
        "recipient": "Propriétaire ou gestionnaire des locaux",
        "subject": "Signalement des dommages et demande de concertation sur le bail",
        "request": (
            "Nous sollicitons un échange rapide afin d’organiser les mesures de sécurité, "
            "les réparations et, si nécessaire, l’examen temporaire des conditions d’exécution du bail."
        ),
        "tasks": [
            "Informer immédiatement le bailleur par écrit.",
            "Vérifier les obligations respectives dans le bail.",
            "Faire constater les dommages.",
            "Coordonner les déclarations d’assurance.",
            "Formaliser par écrit tout accord sur les loyers ou travaux.",
        ],
        "documents": [
            "Bail commercial et état des lieux.",
            "Photos et constats des dommages.",
            "Déclaration de sinistre.",
            "Rapport d’expertise lorsqu’il est disponible.",
            "Devis de sécurisation ou de réparation.",
            "Échanges avec les autorités sur l’accessibilité des locaux.",
        ],
    },
    "Fournisseur": {
        "recipient": "Service commercial ou comptable du fournisseur",
        "subject": "Demande d’aménagement temporaire des conditions de règlement",
        "request": (
            "Nous sollicitons l’étude d’un report, d’un échéancier ou d’une adaptation "
            "temporaire des livraisons, afin de préserver la continuité de la relation commerciale."
        ),
        "tasks": [
            "Lister les factures, commandes et livraisons concernées.",
            "Prioriser les fournisseurs indispensables à la reprise.",
            "Proposer un calendrier de paiement réaliste.",
            "Formaliser tout accord par écrit.",
            "Mettre à jour le plan de trésorerie.",
        ],
        "documents": [
            "Factures et relevé de compte fournisseur.",
            "Commandes ou contrats concernés.",
            "Justificatif de la situation exceptionnelle.",
            "Proposition d’échéancier.",
            "Prévision de reprise d’activité.",
        ],
    },
    "Autre organisme": {
        "recipient": "Service compétent",
        "subject": "Demande d’examen de la situation de l’entreprise",
        "request": (
            "Nous sollicitons l’étude de la situation et des solutions susceptibles "
            "d’être mobilisées au regard des difficultés rencontrées."
        ),
        "tasks": [
            "Identifier le bon interlocuteur et le canal officiel.",
            "Vérifier les délais et conditions de la démarche.",
            "Présenter une demande précise, chiffrée et datée.",
            "Conserver une copie du dossier et l’accusé de réception.",
        ],
        "documents": [
            "Courrier explicatif.",
            "Justificatifs de l’événement et de ses conséquences.",
            "Coordonnées et identifiants de l’entreprise.",
            "Éléments financiers ou administratifs utiles.",
        ],
    },
}


# ============================================================
# STYLE
# ============================================================

def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --cma-red: {CMA_RED};
            --cma-red-dark: {CMA_RED_DARK};
            --background: {BACKGROUND};
            --card: {CARD_BACKGROUND};
            --text: {TEXT_DARK};
            --muted: {TEXT_MUTED};
            --border: {BORDER_COLOR};
        }}

        html, body, [class*="css"] {{
            font-family: Inter, "Segoe UI", Arial, sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 96% 0%, rgba(215,25,32,.055), transparent 26%),
                var(--background);
            color: var(--text);
        }}

        .main .block-container {{
            max-width: 1500px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }}

        /* Sidebar : règles ciblées, sans contaminer la page principale */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #111827 0%, #172235 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }}

        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {{
            color: #FFFFFF;
        }}

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
            color: rgba(255,255,255,.66);
        }}

        [data-testid="stSidebar"] .stRadio label {{
            padding: .42rem .35rem;
            border-radius: 10px;
            transition: all .16s ease;
        }}

        [data-testid="stSidebar"] .stRadio label:hover {{
            background: rgba(255,255,255,.08);
            transform: translateX(3px);
        }}

        [data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,.12);
        }}

        /* Contenu principal : libellés bien visibles */
        [data-testid="stMainBlockContainer"] label,
        [data-testid="stMainBlockContainer"] .stMarkdown p,
        [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] p {{
            color: var(--text);
        }}

        [data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] p {{
            color: #344054 !important;
            font-weight: 650;
        }}

        /* Champs : fond blanc et texte sombre, y compris si le navigateur est en mode sombre */
        [data-testid="stMainBlockContainer"] input,
        [data-testid="stMainBlockContainer"] textarea {{
            background: #FFFFFF !important;
            color: #172033 !important;
            border-color: #D9DEE7 !important;
            caret-color: #172033 !important;
        }}

        [data-testid="stMainBlockContainer"] input::placeholder,
        [data-testid="stMainBlockContainer"] textarea::placeholder {{
            color: #98A2B3 !important;
            opacity: 1 !important;
        }}

        [data-testid="stMainBlockContainer"] div[data-baseweb="select"] > div {{
            background: #FFFFFF !important;
            color: #172033 !important;
            border-color: #D9DEE7 !important;
        }}

        [data-testid="stMainBlockContainer"] div[data-baseweb="select"] span {{
            color: #172033 !important;
        }}

        [data-testid="stMainBlockContainer"] [role="radiogroup"] label p,
        [data-testid="stMainBlockContainer"] [role="checkbox"] + div p {{
            color: #344054 !important;
        }}

        [data-testid="stMainBlockContainer"] button {{
            border-radius: 11px;
            font-weight: 750;
        }}

        [data-testid="stMainBlockContainer"] .stButton > button[kind="primary"],
        [data-testid="stMainBlockContainer"] .stFormSubmitButton > button[kind="primary"] {{
            background: var(--cma-red);
            border-color: var(--cma-red);
            color: white;
        }}

        [data-testid="stMainBlockContainer"] .stButton > button[kind="primary"]:hover,
        [data-testid="stMainBlockContainer"] .stFormSubmitButton > button[kind="primary"]:hover {{
            background: var(--cma-red-dark);
            border-color: var(--cma-red-dark);
        }}

        /* Date picker, multiselect et popovers */
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"] {{
            background: #FFFFFF !important;
            color: #172033 !important;
        }}

        ul[role="listbox"] li,
        ul[role="listbox"] li span {{
            color: #172033 !important;
        }}

        .sidebar-brand {{
            padding: .65rem .2rem 1rem;
        }}
        .sidebar-brand-title {{
            font-size: 1.08rem;
            font-weight: 850;
            color: #FFFFFF;
            line-height: 1.2;
        }}
        .sidebar-brand-subtitle {{
            margin-top: .35rem;
            color: rgba(255,255,255,.68);
            font-size: .76rem;
            line-height: 1.4;
        }}
        .sidebar-red-line {{
            width: 42px;
            height: 4px;
            border-radius: 999px;
            background: var(--cma-red);
            margin-top: .85rem;
        }}

        .app-header {{
            position: relative;
            overflow: hidden;
            padding: 1.55rem 1.75rem;
            margin-bottom: 1.2rem;
            border-radius: 22px;
            background: linear-gradient(125deg, #111827 0%, #1F2937 62%, #35151C 100%);
            box-shadow: 0 16px 36px rgba(16,24,40,.14);
        }}
        .app-header::after {{
            content: "";
            position: absolute;
            top: -70px;
            right: -45px;
            width: 215px;
            height: 215px;
            border-radius: 50%;
            background: rgba(215,25,32,.24);
        }}
        .app-header-kicker {{
            position: relative;
            z-index: 2;
            margin-bottom: .6rem;
            color: #FCA5B5;
            font-size: .75rem;
            font-weight: 850;
            letter-spacing: .1em;
            text-transform: uppercase;
        }}
        .app-header-title {{
            position: relative;
            z-index: 2;
            margin: 0;
            color: #FFFFFF;
            font-size: 2rem;
            font-weight: 850;
            letter-spacing: -.035em;
        }}
        .app-header-subtitle {{
            position: relative;
            z-index: 2;
            max-width: 760px;
            margin-top: .5rem;
            color: rgba(255,255,255,.74);
            font-size: .94rem;
        }}

        .section-title {{
            margin-top: .35rem;
            margin-bottom: .15rem;
            color: var(--text);
            font-size: 1.18rem;
            font-weight: 850;
            letter-spacing: -.02em;
        }}
        .section-subtitle {{
            margin-bottom: .9rem;
            color: var(--muted);
            font-size: .85rem;
        }}

        .kpi-card {{
            min-height: 138px;
            padding: 1.1rem 1.15rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: var(--card);
            box-shadow: 0 7px 22px rgba(16,24,40,.06);
            transition: transform .18s ease, box-shadow .18s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(16,24,40,.10);
        }}
        .kpi-icon {{
            display:flex;
            align-items:center;
            justify-content:center;
            width:42px;
            height:42px;
            margin-bottom:.8rem;
            border-radius:13px;
            font-size:1.15rem;
        }}
        .kpi-label {{
            color:var(--muted);
            font-size:.78rem;
            font-weight:700;
        }}
        .kpi-value {{
            margin-top:.15rem;
            color:var(--text);
            font-size:2rem;
            font-weight:850;
            line-height:1;
        }}
        .kpi-detail {{
            margin-top:.5rem;
            color:var(--muted);
            font-size:.72rem;
        }}

        .alert-card {{
            padding: .95rem;
            margin-bottom: .65rem;
            border: 1px solid #FED3DB;
            border-left: 5px solid var(--cma-red);
            border-radius: 14px;
            background: #FFF8F9;
        }}
        .alert-card-title {{
            color: #871126;
            font-size: .9rem;
            font-weight: 850;
        }}
        .alert-card-meta {{
            margin-top: .28rem;
            color: #7D5560;
            font-size: .75rem;
        }}

        .company-header {{
            padding: 1.2rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: linear-gradient(145deg,#FFFFFF,#F9FAFB);
            box-shadow: 0 8px 24px rgba(16,24,40,.06);
        }}
        .company-name {{
            margin:0;
            color:var(--text);
            font-size:1.4rem;
            font-weight:850;
        }}
        .company-meta {{
            margin-top:.4rem;
            color:var(--muted);
            font-size:.82rem;
        }}
        .status-pill {{
            display:inline-flex;
            align-items:center;
            padding:.32rem .7rem;
            border-radius:999px;
            color:white;
            font-size:.72rem;
            font-weight:850;
        }}

        .timeline-item {{
            position:relative;
            padding:0 0 1.1rem 1.5rem;
            border-left:2px solid #E5E7EB;
        }}
        .timeline-item::before {{
            content:"";
            position:absolute;
            top:.2rem;
            left:-.42rem;
            width:.72rem;
            height:.72rem;
            border:2px solid white;
            border-radius:50%;
            background:var(--cma-red);
            box-shadow:0 0 0 2px #F4B4C0;
        }}
        .timeline-date {{
            color:var(--cma-red);
            font-size:.72rem;
            font-weight:850;
        }}
        .timeline-title {{
            margin-top:.1rem;
            color:var(--text);
            font-size:.88rem;
            font-weight:800;
        }}
        .timeline-description {{
            margin-top:.15rem;
            color:var(--muted);
            font-size:.76rem;
        }}

        .import-box {{
            padding: 1rem 1.1rem;
            border: 1px solid #DDE3EA;
            border-radius: 16px;
            background: linear-gradient(135deg,#FFFFFF,#F8FAFC);
        }}

        div[data-testid="stForm"] {{
            padding: 1.2rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: #FFFFFF;
            box-shadow: 0 7px 22px rgba(16,24,40,.055);
        }}

        [data-testid="stDataFrame"] {{
            overflow:hidden;
            border:1px solid var(--border);
            border-radius:14px;
        }}

        .footer-note {{
            margin-top:2rem;
            padding-top:1rem;
            border-top:1px solid var(--border);
            color:var(--muted);
            font-size:.72rem;
            text-align:center;
        }}

        @media (max-width: 900px) {{
            .app-header-title {{font-size:1.55rem;}}
            .kpi-card {{min-height:120px;}}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DONNÉES DE DÉMONSTRATION
# ============================================================

def get_demo_companies() -> list[dict[str, Any]]:
    now = datetime.now()
    return [
        {
            "id": 1,
            "siren": "521478963",
            "raison_sociale": "Garage de l’Océan",
            "dirigeant": "Thomas Martin",
            "activite": "Réparation automobile",
            "commune": "Le Porge",
            "adresse": "12 avenue de l’Océan",
            "telephone": "05 56 00 00 01",
            "email": "contact@garage-ocean.fr",
            "effectif": 4,
            "statut": "Critique",
            "urgence": "Critique",
            "conseiller": "Marlène",
            "besoins": "Assurance, trésorerie, reprise d’activité",
            "description": "Atelier inaccessible. Matériel endommagé et activité totalement interrompue.",
            "date_contact": now - timedelta(hours=3),
            "date_relance": date.today() + timedelta(days=1),
            "latitude": 44.8729,
            "longitude": -1.0926,
            "historique": [
                {"date": now - timedelta(hours=3), "titre": "Premier contact", "description": "Diagnostic initial réalisé par téléphone."},
                {"date": now - timedelta(hours=2), "titre": "Orientation assurance", "description": "Transmission de la checklist des pièces justificatives."},
            ],
        },
        {
            "id": 2,
            "siren": "798412356",
            "raison_sociale": "Boulangerie des Pins",
            "dirigeant": "Sophie Bernard",
            "activite": "Boulangerie-pâtisserie",
            "commune": "Saumos",
            "adresse": "4 place de la Mairie",
            "telephone": "05 56 00 00 02",
            "email": "bonjour@boulangerie-pins.fr",
            "effectif": 7,
            "statut": "À rappeler",
            "urgence": "Élevée",
            "conseiller": "Romain",
            "besoins": "Pertes d’exploitation, salariés, fournisseurs",
            "description": "Activité très réduite. Difficultés d’approvisionnement et baisse de fréquentation.",
            "date_contact": now - timedelta(days=1, hours=2),
            "date_relance": date.today(),
            "latitude": 44.9028,
            "longitude": -0.9928,
            "historique": [
                {"date": now - timedelta(days=1, hours=2), "titre": "Premier contact", "description": "Évaluation des impacts économiques et sociaux."}
            ],
        },
        {
            "id": 3,
            "siren": "348965217",
            "raison_sociale": "Camping du Lac",
            "dirigeant": "Julien Moreau",
            "activite": "Hébergement touristique",
            "commune": "Lacanau",
            "adresse": "48 route du Lac",
            "telephone": "05 56 00 00 03",
            "email": "direction@campingdulac.fr",
            "effectif": 12,
            "statut": "Accompagnement en cours",
            "urgence": "Élevée",
            "conseiller": "Nadia",
            "besoins": "Annulations, assurance, communication clients",
            "description": "Établissement évacué temporairement. Nombreuses annulations.",
            "date_contact": now - timedelta(days=2),
            "date_relance": date.today() + timedelta(days=2),
            "latitude": 44.9772,
            "longitude": -1.0767,
            "historique": [
                {"date": now - timedelta(days=2), "titre": "Signalement", "description": "Entreprise identifiée par la cellule territoriale."}
            ],
        },
        {
            "id": 4,
            "siren": "695214873",
            "raison_sociale": "Menuiserie Atlantique",
            "dirigeant": "Claire Dubois",
            "activite": "Menuiserie",
            "commune": "Sainte-Hélène",
            "adresse": "7 zone artisanale de Gémeillan",
            "telephone": "05 56 00 00 04",
            "email": "contact@menuiserie-atlantique.fr",
            "effectif": 5,
            "statut": "Activité reprise",
            "urgence": "Modérée",
            "conseiller": "Romain",
            "besoins": "Relance commerciale, fournisseurs",
            "description": "Fermeture préventive de trois jours. L’activité a repris progressivement.",
            "date_contact": now - timedelta(days=4),
            "date_relance": date.today() + timedelta(days=7),
            "latitude": 44.9665,
            "longitude": -0.8841,
            "historique": [
                {"date": now - timedelta(days=1), "titre": "Reprise d’activité", "description": "Réouverture de l’atelier et reprise des chantiers."}
            ],
        },
    ]


def initialize_state() -> None:
    if "companies" not in st.session_state:
        st.session_state.companies = get_demo_companies()
    if "selected_company_id" not in st.session_state:
        st.session_state.selected_company_id = 1
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Tableau de bord"
    if "nav_radio" not in st.session_state:
        st.session_state.nav_radio = st.session_state.current_page
    if "cellule_name" not in st.session_state:
        st.session_state.cellule_name = "Cellule de crise Gironde"
    if "current_advisor" not in st.session_state:
        st.session_state.current_advisor = "Romain"


# ============================================================
# OUTILS
# ============================================================

def companies_dataframe() -> pd.DataFrame:
    rows = []
    for c in st.session_state.companies:
        rows.append({
            "ID": c["id"],
            "SIREN": c["siren"],
            "Entreprise": c["raison_sociale"],
            "Activité": c["activite"],
            "Commune": c["commune"],
            "Statut": c["statut"],
            "Urgence": c["urgence"],
            "Conseiller": c["conseiller"],
            "Dernier contact": c["date_contact"],
            "Relance": c["date_relance"],
            "Latitude": c["latitude"],
            "Longitude": c["longitude"],
        })
    return pd.DataFrame(rows)


def get_company(company_id: int) -> dict[str, Any] | None:
    return next((c for c in st.session_state.companies if c["id"] == company_id), None)


def format_datetime(value: datetime | None) -> str:
    return "Non renseigné" if value is None else value.strftime("%d/%m/%Y à %H:%M")


def format_date(value: date | None) -> str:
    return "Aucune" if value is None else value.strftime("%d/%m/%Y")


def normalize_siren(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().replace(" ", "").replace(".0", "")
    return "".join(ch for ch in text if ch.isdigit())


def normalize_text(value: Any) -> str:
    return "" if pd.isna(value) else str(value).strip()


def parse_date(value: Any) -> date:
    if pd.isna(value) or value == "":
        return date.today()
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    return date.today() if pd.isna(parsed) else parsed.date()


def coordinates_for_commune(commune: str) -> tuple[float, float]:
    if commune in COMMUNES_COORDONNEES:
        return COMMUNES_COORDONNEES[commune]
    # Point neutre Bordeaux si commune non reconnue
    return COMMUNES_COORDONNEES["Bordeaux"]


def create_excel_template() -> bytes:
    template = pd.DataFrame([
        {
            "SIREN": "123456789",
            "Raison sociale": "Entreprise exemple",
            "Commune": "Lacanau",
            "Téléphone": "05 56 00 00 00",
            "Email": "contact@exemple.fr",
            "Activité": "Menuiserie",
            "Conseiller": "Romain",
            "Date de rappel": (date.today() + timedelta(days=1)).strftime("%d/%m/%Y"),
        }
    ])
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        template.to_excel(writer, index=False, sheet_name="Entreprises")
    return buffer.getvalue()


def read_import_file(uploaded_file) -> tuple[pd.DataFrame | None, list[str]]:
    errors: list[str] = []
    try:
        df = pd.read_excel(uploaded_file, dtype={"SIREN": str})
    except Exception as exc:
        return None, [f"Impossible de lire le fichier Excel : {exc}"]

    df.columns = [str(col).strip() for col in df.columns]
    missing = [col for col in IMPORT_COLUMNS if col not in df.columns]
    if missing:
        errors.append("Colonnes manquantes : " + ", ".join(missing))
        return None, errors

    df = df[IMPORT_COLUMNS].copy()
    df["SIREN"] = df["SIREN"].apply(normalize_siren)
    for col in ["Raison sociale", "Commune", "Téléphone", "Email", "Activité", "Conseiller"]:
        df[col] = df[col].apply(normalize_text)
    df["Date de rappel"] = df["Date de rappel"].apply(parse_date)

    empty_names = df["Raison sociale"].eq("")
    if empty_names.any():
        errors.append(f"{int(empty_names.sum())} ligne(s) sans raison sociale seront ignorées.")

    invalid_siren = ~df["SIREN"].str.match(r"^\d{9}$", na=False)
    if invalid_siren.any():
        errors.append(f"{int(invalid_siren.sum())} ligne(s) ont un SIREN absent ou invalide.")

    return df, errors


def import_companies_from_dataframe(df: pd.DataFrame) -> tuple[int, int, list[str]]:
    existing_sirens = {normalize_siren(c["siren"]) for c in st.session_state.companies}
    next_id = max((c["id"] for c in st.session_state.companies), default=0) + 1
    imported = 0
    skipped = 0
    messages: list[str] = []

    for index, row in df.iterrows():
        name = normalize_text(row["Raison sociale"])
        siren = normalize_siren(row["SIREN"])

        if not name:
            skipped += 1
            messages.append(f"Ligne {index + 2} ignorée : raison sociale absente.")
            continue

        if not siren or len(siren) != 9:
            skipped += 1
            messages.append(f"Ligne {index + 2} ignorée : SIREN invalide.")
            continue

        if siren in existing_sirens:
            skipped += 1
            messages.append(f"Ligne {index + 2} ignorée : SIREN {siren} déjà présent.")
            continue

        commune = normalize_text(row["Commune"]) or "Bordeaux"
        lat, lon = coordinates_for_commune(commune)
        advisor = normalize_text(row["Conseiller"]) or st.session_state.current_advisor

        company = {
            "id": next_id,
            "siren": siren,
            "raison_sociale": name,
            "dirigeant": "Non renseigné",
            "activite": normalize_text(row["Activité"]) or "Non renseignée",
            "commune": commune,
            "adresse": "Non renseignée",
            "telephone": normalize_text(row["Téléphone"]) or "Non renseigné",
            "email": normalize_text(row["Email"]) or "Non renseigné",
            "effectif": 0,
            "statut": "À rappeler",
            "urgence": "Modérée",
            "conseiller": advisor,
            "besoins": "À qualifier lors du rappel",
            "description": "Entreprise importée depuis la liste Excel des entreprises à rappeler.",
            "date_contact": datetime.now(),
            "date_relance": parse_date(row["Date de rappel"]),
            "latitude": lat,
            "longitude": lon,
            "historique": [{
                "date": datetime.now(),
                "titre": "Import Excel",
                "description": "Entreprise ajoutée à la liste des rappels.",
            }],
        }

        st.session_state.companies.append(company)
        existing_sirens.add(siren)
        next_id += 1
        imported += 1

    return imported, skipped, messages



def daily_contacts_dataframe(selected_date: date) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for company in st.session_state.companies:
        last_contact = company.get("date_contact")
        if not isinstance(last_contact, datetime) or last_contact.date() != selected_date:
            continue

        rows.append(
            {
                "Date du contact": last_contact.strftime("%d/%m/%Y"),
                "Heure": last_contact.strftime("%H:%M"),
                "SIREN": company.get("siren", ""),
                "Raison sociale": company.get("raison_sociale", ""),
                "Activité": company.get("activite", ""),
                "Commune": company.get("commune", ""),
                "Téléphone": company.get("telephone", ""),
                "Email": company.get("email", ""),
                "Statut": company.get("statut", ""),
                "Urgence": company.get("urgence", ""),
                "Conseiller": company.get("conseiller", ""),
                "Besoins identifiés": company.get("besoins", ""),
                "Prochaine relance": format_date(company.get("date_relance")),
                "Synthèse": company.get("description", ""),
            }
        )

    return pd.DataFrame(rows)


def create_daily_contacts_excel(selected_date: date) -> tuple[bytes, pd.DataFrame]:
    export_df = daily_contacts_dataframe(selected_date)
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Entreprises contactées")

        worksheet = writer.sheets["Entreprises contactées"]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        widths = {
            "A": 16, "B": 10, "C": 14, "D": 30, "E": 28, "F": 24,
            "G": 18, "H": 30, "I": 26, "J": 14, "K": 20, "L": 40,
            "M": 18, "N": 55,
        }
        for column, width in widths.items():
            worksheet.column_dimensions[column].width = width

    return buffer.getvalue(), export_df


def sync_page_from_navigation() -> None:
    st.session_state.current_page = st.session_state.nav_radio

def calculate_urgency_score(interruption: str, degats: str, tresorerie: str, salaries: str, accessibilite: str) -> tuple[int, str]:
    score = 0
    score += {"Aucune": 0, "Partielle": 2, "Totale": 4}.get(interruption, 0)
    score += {"Aucun": 0, "Légers": 1, "Importants": 3, "Destruction majeure": 5}.get(degats, 0)
    score += {"Pas de difficulté immédiate": 0, "Tension dans le mois": 2, "Risque sous 15 jours": 4, "Situation immédiate critique": 5}.get(tresorerie, 0)
    score += {"Non concerné": 0, "Organisation maintenue": 1, "Activité partielle envisagée": 3, "Emplois directement menacés": 5}.get(salaries, 0)
    score += {"Accessible": 0, "Accès limité": 2, "Zone inaccessible": 4}.get(accessibilite, 0)

    if score >= 16:
        level = "Critique"
    elif score >= 10:
        level = "Élevée"
    elif score >= 5:
        level = "Modérée"
    else:
        level = "Faible"
    return score, level


def urgency_to_status(level: str) -> str:
    return {"Critique": "Critique", "Élevée": "Accompagnement en cours", "Modérée": "À rappeler", "Faible": "Accompagnement en cours"}.get(level, "Accompagnement en cours")


def build_map_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    map_df = df.copy()
    map_df["Couleur"] = map_df["Statut"].map(STATUS_COLORS)
    map_df["Rayon"] = map_df["Urgence"].map({"Faible": 170, "Modérée": 230, "Élevée": 300, "Critique": 380}).fillna(230)
    return map_df


def render_map(df: pd.DataFrame, height: int = 480, zoom: float = 8.7) -> None:
    if df.empty:
        st.info("Aucun point ne correspond aux filtres sélectionnés.")
        return

    map_df = build_map_dataframe(df)
    center_lat = float(map_df["Latitude"].mean())
    center_lon = float(map_df["Longitude"].mean())

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[Longitude, Latitude]",
        get_fill_color="Couleur",
        get_line_color=[255, 255, 255, 230],
        get_radius="Rayon",
        radius_min_pixels=8,
        radius_max_pixels=22,
        line_width_min_pixels=2,
        pickable=True,
        opacity=0.92,
        stroked=True,
        filled=True,
    )

    deck = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=0),
        layers=[layer],
        tooltip={
            "html": """
            <div style="min-width:220px;font-family:Arial,sans-serif">
                <div style="font-size:15px;font-weight:800;margin-bottom:7px">{Entreprise}</div>
                <div><b>Commune :</b> {Commune}</div>
                <div><b>Activité :</b> {Activité}</div>
                <div><b>Statut :</b> {Statut}</div>
                <div><b>Urgence :</b> {Urgence}</div>
                <div><b>Conseiller :</b> {Conseiller}</div>
            </div>
            """,
            "style": {"backgroundColor": "#111827", "color": "white", "borderRadius": "12px", "padding": "12px"},
        },
    )
    st.pydeck_chart(deck, height=height, use_container_width=True)


def render_header(title: str, subtitle: str, kicker: str = "Cellule de crise") -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-header-kicker">● {kicker}</div>
            <h1 class="app-header-title">{title}</h1>
            <div class="app-header-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="section-title">{title}</div><div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_kpi(label: str, value: int | str, icon: str, detail: str, background_color: str, icon_color: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:{background_color};color:{icon_color};">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_legend() -> None:
    html = ""
    for status, color in STATUS_HEX.items():
        html += f'<span style="display:inline-flex;align-items:center;margin-right:14px;margin-bottom:6px;font-size:12px;color:#667085"><span style="width:9px;height:9px;border-radius:50%;background:{color};margin-right:5px"></span>{status}</span>'
    st.markdown(html, unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown('<div class="footer-note">CMA Urgence Entreprises · V1.2 · Données temporaires de session</div>', unsafe_allow_html=True)


def navigate_to(page: str, company_id: int | None = None) -> None:
    st.session_state.current_page = page
    st.session_state.nav_radio = page
    if company_id is not None:
        st.session_state.selected_company_id = company_id
    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">🚨 CMA Urgence<br>Entreprises</div>
                <div class="sidebar-brand-subtitle">Pilotage et accompagnement des entreprises impactées par une situation de crise.</div>
                <div class="sidebar-red-line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pages = ["Tableau de bord", "Nouveau diagnostic", "Entreprises", "Cartographie", "Statistiques", "Courriers", "Paramètres"]
        icons = {
            "Tableau de bord": "🏠",
            "Nouveau diagnostic": "➕",
            "Entreprises": "🏢",
            "Cartographie": "🗺️",
            "Statistiques": "📊",
            "Courriers": "📄",
            "Paramètres": "⚙️",
        }
        if st.session_state.nav_radio not in pages:
            st.session_state.nav_radio = "Tableau de bord"

        st.radio(
            "Navigation",
            pages,
            key="nav_radio",
            format_func=lambda item: f"{icons[item]}  {item}",
            label_visibility="collapsed",
            on_change=sync_page_from_navigation,
        )
        page = st.session_state.nav_radio

        st.divider()
        st.caption("CELLULE ACTIVE")
        st.markdown(
            f"""
            <div style="padding:.85rem;border:1px solid rgba(255,255,255,.12);border-radius:13px;background:rgba(255,255,255,.055)">
                <div style="font-size:.73rem;color:rgba(255,255,255,.58)">Dispositif</div>
                <div style="margin-top:.18rem;font-size:.88rem;font-weight:800">{st.session_state.cellule_name}</div>
                <div style="margin-top:.7rem;font-size:.73rem;color:rgba(255,255,255,.58)">Conseiller</div>
                <div style="margin-top:.18rem;font-size:.84rem;font-weight:700">👤 {st.session_state.current_advisor}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Prototype : les données ne sont pas encore partagées entre les conseillers.")
    return page


# ============================================================
# TABLEAU DE BORD
# ============================================================

def page_dashboard() -> None:
    render_header(APP_NAME, "Vue consolidée de la situation, des entreprises suivies et des actions prioritaires.", "Centre de commandement")
    df = companies_dataframe()

    total = len(df)
    critiques = int((df["Statut"] == "Critique").sum())
    relances = int(df["Relance"].apply(lambda v: v is not None and v <= date.today()).sum())
    reprises = int(df["Statut"].isin(["Activité reprise", "Clôturé"]).sum())

    cols = st.columns(4)
    with cols[0]:
        render_kpi("Entreprises suivies", total, "🏢", "Dossiers enregistrés", "#EEF4FF", "#2671DD")
    with cols[1]:
        render_kpi("Relances à effectuer", relances, "☎️", "Échéance atteinte", "#FFF5E6", "#D97800")
    with cols[2]:
        render_kpi("Situations critiques", critiques, "🚨", "Intervention prioritaire", "#FFF0F3", CMA_RED)
    with cols[3]:
        render_kpi("Reprises ou clôtures", reprises, "✅", "Évolution favorable", "#ECFDF3", "#168A47")

    st.write("")
    map_col, alert_col = st.columns([2.25, 1], gap="large")

    with map_col:
        render_section_title("Cartographie opérationnelle", "Position et niveau de priorité des entreprises accompagnées.")
        render_status_legend()
        render_map(df, height=480)

    with alert_col:
        render_section_title("Situations prioritaires", "Dossiers nécessitant une attention rapide.")
        priority = df[df["Statut"].isin(["Critique", "À rappeler"])].head(5)
        for _, row in priority.iterrows():
            st.markdown(
                f'<div class="alert-card"><div class="alert-card-title">{row["Entreprise"]}</div><div class="alert-card-meta">📍 {row["Commune"]}<br>🚨 {row["Urgence"]} · {row["Statut"]}<br>👤 {row["Conseiller"]}</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Ouvrir le dossier", key=f"open_{row['ID']}", use_container_width=True):
                navigate_to("Entreprises", int(row["ID"]))

    st.write("")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        commune_df = df.groupby("Commune").size().reset_index(name="Entreprises").sort_values("Entreprises")
        fig = px.bar(commune_df, x="Entreprises", y="Commune", orientation="h", text="Entreprises")
        fig.update_traces(marker_color=CMA_RED, textposition="outside")
        fig.update_layout(height=340, margin=dict(l=5, r=25, t=25, b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="", yaxis_title="", title="Entreprises par commune")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with c2:
        status_df = df.groupby("Statut").size().reset_index(name="Entreprises")
        fig = px.pie(status_df, names="Statut", values="Entreprises", hole=.65, color="Statut", color_discrete_map=STATUS_HEX)
        fig.update_layout(height=340, margin=dict(l=5, r=5, t=25, b=5), paper_bgcolor="rgba(0,0,0,0)", title="Répartition par statut")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    render_footer()


# ============================================================
# DIAGNOSTIC
# ============================================================

def page_diagnostic() -> None:
    render_header("Nouveau diagnostic", "Qualifier la situation de l’entreprise et préparer le plan d’action.", "Accompagnement")
    st.info("Le diagnostic calcule automatiquement un niveau d’urgence. Le résultat pourra être ajusté dans la fiche entreprise.")

    with st.form("diagnostic_form"):
        render_section_title("1. Identification de l’entreprise", "Renseignez les informations principales.")
        c1, c2, c3 = st.columns(3)
        with c1:
            raison_sociale = st.text_input("Raison sociale *")
            siren = st.text_input("SIREN", max_chars=9)
            dirigeant = st.text_input("Dirigeant")
        with c2:
            activite = st.text_input("Activité *")
            commune = st.selectbox("Commune *", list(COMMUNES_COORDONNEES.keys()))
            adresse = st.text_input("Adresse")
        with c3:
            telephone = st.text_input("Téléphone")
            email = st.text_input("E-mail")
            effectif = st.number_input("Effectif", min_value=0, max_value=999, value=1)

        st.divider()
        render_section_title("2. Évaluation des impacts", "Les réponses permettent d’estimer le niveau de priorité.")
        c1, c2 = st.columns(2)
        with c1:
            interruption = st.radio("Interruption d’activité", ["Aucune", "Partielle", "Totale"], horizontal=True)
            degats = st.select_slider("Dégâts matériels", options=["Aucun", "Légers", "Importants", "Destruction majeure"], value="Légers")
            accessibilite = st.radio("Accessibilité de l’établissement", ["Accessible", "Accès limité", "Zone inaccessible"])
        with c2:
            tresorerie = st.selectbox("Situation de trésorerie", ["Pas de difficulté immédiate", "Tension dans le mois", "Risque sous 15 jours", "Situation immédiate critique"])
            salaries = st.selectbox("Situation des salariés", ["Non concerné", "Organisation maintenue", "Activité partielle envisagée", "Emplois directement menacés"])
            date_relance = st.date_input("Date de relance souhaitée", value=date.today() + timedelta(days=2))

        st.divider()
        render_section_title("3. Besoins et compte rendu", "Décrivez la situation avec les mots de l’entreprise.")
        besoins = st.multiselect("Besoins identifiés", ["Assurance", "Trésorerie", "Banque", "URSSAF", "DGFIP", "Activité partielle", "Salariés", "Fournisseurs", "Clients", "Relogement de l’activité", "Reprise d’activité", "Communication", "Autre"])
        description = st.text_area("Description de la situation *", height=140)
        conseiller = st.text_input("Conseiller en charge", value=st.session_state.current_advisor)
        submitted = st.form_submit_button("Enregistrer le diagnostic", type="primary", use_container_width=True)

    if submitted:
        if not raison_sociale.strip() or not activite.strip() or not description.strip():
            st.error("La raison sociale, l’activité et la description sont obligatoires.")
            return
        if siren and (not siren.isdigit() or len(siren) != 9):
            st.error("Le SIREN doit contenir exactement 9 chiffres.")
            return
        if siren and any(normalize_siren(c["siren"]) == siren for c in st.session_state.companies):
            st.error("Ce SIREN existe déjà.")
            return

        score, urgency = calculate_urgency_score(interruption, degats, tresorerie, salaries, accessibilite)
        lat, lon = coordinates_for_commune(commune)
        new_id = max(c["id"] for c in st.session_state.companies) + 1

        company = {
            "id": new_id,
            "siren": siren or f"DEMO{new_id:05d}",
            "raison_sociale": raison_sociale.strip(),
            "dirigeant": dirigeant.strip() or "Non renseigné",
            "activite": activite.strip(),
            "commune": commune,
            "adresse": adresse.strip() or "Non renseignée",
            "telephone": telephone.strip() or "Non renseigné",
            "email": email.strip() or "Non renseigné",
            "effectif": int(effectif),
            "statut": urgency_to_status(urgency),
            "urgence": urgency,
            "conseiller": conseiller.strip() or "Non attribué",
            "besoins": ", ".join(besoins) if besoins else "À préciser",
            "description": description.strip(),
            "date_contact": datetime.now(),
            "date_relance": date_relance,
            "latitude": lat,
            "longitude": lon,
            "historique": [{"date": datetime.now(), "titre": "Diagnostic initial", "description": f"Score d’urgence : {score}/23."}],
        }
        st.session_state.companies.append(company)
        st.session_state.selected_company_id = new_id
        st.success(f"Diagnostic enregistré : urgence {urgency}, score {score}/23.")
        if st.button("Ouvrir le dossier", type="primary"):
            navigate_to("Entreprises", new_id)


# ============================================================
# ENTREPRISES + IMPORT EXCEL
# ============================================================

def page_companies() -> None:
    render_header("Entreprises accompagnées", "Consulter, filtrer et importer les entreprises à rappeler.", "Portefeuille")

    with st.expander("📥 Importer une liste Excel d’entreprises à rappeler", expanded=False):
        st.markdown('<div class="import-box">', unsafe_allow_html=True)
        st.write("Le fichier doit contenir les colonnes suivantes :")
        st.code("SIREN | Raison sociale | Commune | Téléphone | Email | Activité | Conseiller | Date de rappel")

        st.download_button(
            "Télécharger le modèle Excel",
            data=create_excel_template(),
            file_name="modele_entreprises_a_rappeler.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        uploaded = st.file_uploader("Sélectionner le fichier Excel", type=["xlsx"], key="company_excel_import")

        if uploaded is not None:
            preview_df, warnings = read_import_file(uploaded)
            if warnings:
                for warning in warnings:
                    st.warning(warning)

            if preview_df is not None:
                st.write("Aperçu avant import")
                st.dataframe(preview_df, use_container_width=True, hide_index=True)

                valid_count = int(
                    preview_df["Raison sociale"].ne("").sum()
                    - ((~preview_df["SIREN"].str.match(r"^\d{9}$", na=False)) & preview_df["Raison sociale"].ne("")).sum()
                )
                st.caption(f"{max(valid_count, 0)} ligne(s) potentiellement importable(s).")

                if st.button("Importer les entreprises", type="primary", use_container_width=True):
                    imported, skipped, messages = import_companies_from_dataframe(preview_df)
                    if imported:
                        st.success(f"{imported} entreprise(s) importée(s). Elles apparaissent maintenant avec le statut « À rappeler ».")
                    if skipped:
                        st.warning(f"{skipped} ligne(s) ignorée(s).")
                    if messages:
                        with st.expander("Détail des lignes ignorées"):
                            for message in messages:
                                st.write("• " + message)
                    if imported:
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    df = companies_dataframe()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        search = st.text_input("Rechercher", placeholder="Entreprise, SIREN, commune…")
    with c2:
        statuses = st.multiselect("Statut", list(STATUS_COLORS.keys()))
    with c3:
        communes = st.multiselect("Commune", sorted(df["Commune"].dropna().unique()))
    with c4:
        advisors = st.multiselect("Conseiller", sorted(df["Conseiller"].dropna().unique()))

    filtered = df.copy()
    if search:
        q = search.casefold()
        mask = (
            filtered["Entreprise"].str.casefold().str.contains(q, na=False)
            | filtered["SIREN"].astype(str).str.casefold().str.contains(q, na=False)
            | filtered["Commune"].str.casefold().str.contains(q, na=False)
            | filtered["Activité"].str.casefold().str.contains(q, na=False)
        )
        filtered = filtered[mask]
    if statuses:
        filtered = filtered[filtered["Statut"].isin(statuses)]
    if communes:
        filtered = filtered[filtered["Commune"].isin(communes)]
    if advisors:
        filtered = filtered[filtered["Conseiller"].isin(advisors)]

    render_section_title(f"Résultats — {len(filtered)} entreprise(s)", "Sélectionnez une entreprise pour consulter sa fiche.")

    display = filtered[["Entreprise", "SIREN", "Commune", "Activité", "Statut", "Urgence", "Conseiller", "Dernier contact", "Relance"]].copy()
    display["Dernier contact"] = pd.to_datetime(display["Dernier contact"]).dt.strftime("%d/%m/%Y %H:%M")
    display["Relance"] = display["Relance"].apply(format_date)
    st.dataframe(display, use_container_width=True, hide_index=True, height=330)

    if filtered.empty:
        return

    options = {f"{row['Entreprise']} — {row['Commune']}": int(row["ID"]) for _, row in filtered.iterrows()}
    current_id = st.session_state.selected_company_id
    default_label = next((label for label, cid in options.items() if cid == current_id), next(iter(options)))
    label = st.selectbox("Ouvrir une fiche entreprise", list(options.keys()), index=list(options.keys()).index(default_label))
    selected_id = options[label]
    st.session_state.selected_company_id = selected_id
    company = get_company(selected_id)
    if company:
        render_company_record(company)


def render_company_record(company: dict[str, Any]) -> None:
    status_color = STATUS_HEX.get(company["statut"], "#667085")
    st.markdown(
        f"""
        <div class="company-header">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap">
                <div>
                    <h2 class="company-name">{company["raison_sociale"]}</h2>
                    <div class="company-meta">{company["activite"]} · {company["commune"]} · SIREN {company["siren"]}</div>
                </div>
                <span class="status-pill" style="background:{status_color}">{company["statut"]}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.markdown(f"""
        **Dirigeant**  
        {company["dirigeant"]}

        **Téléphone**  
        {company["telephone"]}

        **E-mail**  
        {company["email"]}

        **Adresse**  
        {company["adresse"]}, {company["commune"]}

        **Effectif**  
        {company["effectif"]}

        **Conseiller**  
        {company["conseiller"]}

        **Prochaine relance**  
        {format_date(company["date_relance"])}

        **Besoins identifiés**  
        {company["besoins"]}

        **Synthèse**  
        {company["description"]}
        """)

    with right:
        with st.form(f"update_{company['id']}"):
            new_status = st.selectbox("Statut", list(STATUS_COLORS.keys()), index=list(STATUS_COLORS.keys()).index(company["statut"]))
            new_urgency = st.selectbox("Urgence", URGENCY_LEVELS, index=URGENCY_LEVELS.index(company["urgence"]))
            new_follow_up = st.date_input("Prochaine relance", value=company["date_relance"] or date.today() + timedelta(days=3))
            action_title = st.text_input("Action réalisée")
            action_description = st.text_area("Commentaire", height=90)
            submitted = st.form_submit_button("Enregistrer la mise à jour", type="primary", use_container_width=True)

        if submitted:
            company["statut"] = new_status
            company["urgence"] = new_urgency
            company["date_relance"] = new_follow_up
            company["date_contact"] = datetime.now()
            if action_title.strip():
                company["historique"].insert(0, {"date": datetime.now(), "titre": action_title.strip(), "description": action_description.strip() or "Aucun commentaire."})
            st.success("Dossier mis à jour.")
            st.rerun()

    render_section_title("Historique du dossier", "Chronologie des contacts et démarches.")
    for item in sorted(company["historique"], key=lambda x: x["date"], reverse=True):
        st.markdown(
            f'<div class="timeline-item"><div class="timeline-date">{format_datetime(item["date"])}</div><div class="timeline-title">{item["titre"]}</div><div class="timeline-description">{item["description"]}</div></div>',
            unsafe_allow_html=True,
        )


# ============================================================
# CARTOGRAPHIE
# ============================================================

def page_map() -> None:
    render_header("Cartographie collaborative", "Visualiser la répartition territoriale des entreprises.", "Pilotage territorial")
    df = companies_dataframe()
    c1, c2, c3 = st.columns(3)
    with c1:
        statuses = st.multiselect("Statuts", list(STATUS_COLORS.keys()), default=list(STATUS_COLORS.keys()))
    with c2:
        urgencies = st.multiselect("Niveaux d’urgence", URGENCY_LEVELS, default=URGENCY_LEVELS)
    with c3:
        advisors = st.multiselect("Conseillers", sorted(df["Conseiller"].unique()), default=sorted(df["Conseiller"].unique()))

    filtered = df[df["Statut"].isin(statuses) & df["Urgence"].isin(urgencies) & df["Conseiller"].isin(advisors)]
    k1, k2, k3 = st.columns(3)
    k1.metric("Points affichés", len(filtered))
    k2.metric("Communes concernées", filtered["Commune"].nunique())
    k3.metric("Entreprises à rappeler", int((filtered["Statut"] == "À rappeler").sum()))
    render_status_legend()
    render_map(filtered, height=650)


# ============================================================
# STATISTIQUES
# ============================================================

def page_statistics() -> None:
    render_header(
        "Statistiques entreprises",
        "Analyser la situation des entreprises accompagnées et exporter l’activité quotidienne.",
        "Analyse",
    )

    df = companies_dataframe()
    details = pd.DataFrame(st.session_state.companies)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        urgency_df = (
            df.groupby("Urgence")
            .size()
            .reindex(URGENCY_LEVELS, fill_value=0)
            .reset_index(name="Entreprises")
        )
        fig = px.bar(
            urgency_df,
            x="Urgence",
            y="Entreprises",
            text="Entreprises",
            color="Urgence",
            color_discrete_map={
                "Faible": "#16A34A",
                "Modérée": "#F2B705",
                "Élevée": "#F19100",
                "Critique": CMA_RED,
            },
        )
        fig.update_layout(
            height=370,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title="Répartition par niveau d’urgence",
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        status_df = df.groupby("Statut").size().reset_index(name="Entreprises")
        fig = px.pie(
            status_df,
            names="Statut",
            values="Entreprises",
            hole=0.62,
            color="Statut",
            color_discrete_map=STATUS_HEX,
        )
        fig.update_layout(
            height=370,
            paper_bgcolor="rgba(0,0,0,0)",
            title="Répartition par statut",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    c3, c4 = st.columns(2, gap="large")

    with c3:
        commune_df = (
            df.groupby("Commune")
            .size()
            .reset_index(name="Entreprises")
            .sort_values("Entreprises", ascending=True)
        )
        fig = px.bar(
            commune_df,
            x="Entreprises",
            y="Commune",
            orientation="h",
            text="Entreprises",
        )
        fig.update_traces(marker_color=CMA_RED, textposition="outside")
        fig.update_layout(
            height=390,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title="Entreprises par commune",
            xaxis_title="",
            yaxis_title="",
            margin=dict(l=5, r=30, t=50, b=5),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c4:
        activity_df = (
            details.groupby("activite")
            .size()
            .reset_index(name="Entreprises")
            .sort_values("Entreprises", ascending=True)
            .tail(10)
        )
        fig = px.bar(
            activity_df,
            x="Entreprises",
            y="activite",
            orientation="h",
            text="Entreprises",
        )
        fig.update_traces(marker_color="#2671DD", textposition="outside")
        fig.update_layout(
            height=390,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title="Principales activités représentées",
            xaxis_title="",
            yaxis_title="",
            margin=dict(l=5, r=30, t=50, b=5),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.divider()
    render_section_title(
        "Export journalier des entreprises contactées",
        "Choisissez une date pour télécharger la liste des entreprises dont le dernier contact a été enregistré ce jour-là.",
    )

    export_date = st.date_input(
        "Journée à exporter",
        value=date.today(),
        key="daily_export_date",
    )
    excel_data, export_df = create_daily_contacts_excel(export_date)

    m1, m2, m3 = st.columns(3)
    m1.metric("Entreprises contactées", len(export_df))
    m2.metric(
        "Situations critiques",
        int((export_df["Statut"] == "Critique").sum()) if not export_df.empty else 0,
    )
    m3.metric(
        "Relances renseignées",
        int(export_df["Prochaine relance"].ne("Aucune").sum()) if not export_df.empty else 0,
    )

    if export_df.empty:
        st.info("Aucun dernier contact n’est enregistré pour cette journée.")
    else:
        st.dataframe(export_df, use_container_width=True, hide_index=True, height=300)
        st.download_button(
            "Télécharger l’export Excel de la journée",
            data=excel_data,
            file_name=f"entreprises_contactees_{export_date.strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

    st.caption(
        "Dans cette version sans base de données, l’export repose sur la date du dernier contact enregistrée dans chaque fiche."
    )


# ============================================================
# COURRIERS
# ============================================================

def build_letter(company: dict[str, Any], recipient: str, subject: str, request: str, advisor: str) -> str:
    return f"""{company["raison_sociale"]}
{company["adresse"]}
{company["commune"]}

À l’attention de :
{recipient}

Le {date.today().strftime("%d/%m/%Y")}

Objet : {subject}

Madame, Monsieur,

L’entreprise {company["raison_sociale"]}, exerçant une activité de {company["activite"]} à {company["commune"]}, rencontre actuellement des difficultés à la suite de la situation de crise ayant affecté son territoire.

Situation constatée :

{company["description"]}

Besoins identifiés :

{company["besoins"]}

Demande :

{request}

L’entreprise reste disponible pour transmettre tout document justificatif nécessaire à l’étude de sa situation.

Veuillez agréer, Madame, Monsieur, l’expression de nos salutations distinguées.

{company["dirigeant"]}
Pour {company["raison_sociale"]}

Courrier préparé avec l’appui de :
{advisor}
CMA Nouvelle-Aquitaine
"""


def page_letters() -> None:
    render_header(
        "Courriers et démarches",
        "Préparer le courrier, la liste des actions et les pièces à transmettre selon l’organisme.",
        "Documents",
    )

    options = {
        f"{company['raison_sociale']} — {company['commune']}": company["id"]
        for company in st.session_state.companies
    }
    selected_label = st.selectbox("Entreprise", list(options.keys()))
    company = get_company(options[selected_label])

    organism = st.selectbox(
        "Organisme destinataire",
        list(ORGANISM_GUIDES.keys()),
        key="selected_organism",
    )
    guide = ORGANISM_GUIDES[organism]

    info_col, docs_col = st.columns(2, gap="large")

    with info_col:
        render_section_title(
            "To-do list conseillée",
            "Étapes de préparation et de suivi à adapter à la situation réelle.",
        )
        for index, task in enumerate(guide["tasks"], start=1):
            st.checkbox(task, key=f"task_{organism}_{index}")

    with docs_col:
        render_section_title(
            "Documents à préparer ou à joindre",
            "La liste reste indicative : vérifiez les demandes précises de l’organisme.",
        )
        for index, document in enumerate(guide["documents"], start=1):
            st.checkbox(document, key=f"doc_{organism}_{index}")

    st.divider()
    edit_col, preview_col = st.columns([1, 1.35], gap="large")

    with edit_col:
        recipient = st.text_input(
            "Destinataire",
            value=guide["recipient"],
            key=f"recipient_{organism}",
        )
        subject = st.text_input(
            "Objet",
            value=guide["subject"],
            key=f"subject_{organism}",
        )
        request = st.text_area(
            "Demande formulée",
            value=guide["request"],
            height=170,
            key=f"request_{organism}",
        )
        advisor = st.text_input(
            "Conseiller",
            value=st.session_state.current_advisor,
            key="letter_advisor",
        )

    letter = build_letter(company, recipient, subject, request, advisor)

    with preview_col:
        st.text_area(
            "Aperçu du courrier",
            value=letter,
            height=535,
            key=f"preview_{company['id']}_{organism}",
        )
        st.download_button(
            "Télécharger le courrier",
            data=letter.encode("utf-8"),
            file_name=(
                f"courrier_{organism}_{company['raison_sociale']}.txt"
                .lower()
                .replace(" ", "_")
                .replace("/", "_")
            ),
            mime="text/plain",
            type="primary",
            use_container_width=True,
        )

    st.warning(
        "Les démarches et pièces proposées sont des aides à la préparation. "
        "Le conseiller doit vérifier les règles, délais et demandes en vigueur avant tout envoi."
    )


# ============================================================
# PARAMÈTRES
# ============================================================

def page_settings() -> None:
    render_header("Paramètres", "Configurer la cellule et l’utilisateur courant.", "Administration")
    with st.form("settings"):
        cell = st.text_input("Nom de la cellule", value=st.session_state.cellule_name)
        advisor = st.text_input("Conseiller courant", value=st.session_state.current_advisor)
        save = st.form_submit_button("Enregistrer", type="primary")
    if save:
        st.session_state.cellule_name = cell.strip() or "Cellule de crise"
        st.session_state.current_advisor = advisor.strip() or "Conseiller CMA"
        st.success("Paramètres enregistrés.")
        st.rerun()

    st.divider()
    if st.button("Réinitialiser les données de démonstration"):
        st.session_state.companies = get_demo_companies()
        st.session_state.selected_company_id = 1
        st.rerun()

    st.info("Les données sont encore stockées dans la session Streamlit. Une base partagée sera nécessaire pour un vrai fonctionnement multi-utilisateurs.")


# ============================================================
# APPLICATION
# ============================================================

def main() -> None:
    inject_css()
    initialize_state()
    page = render_sidebar()

    if page == "Tableau de bord":
        page_dashboard()
    elif page == "Nouveau diagnostic":
        page_diagnostic()
    elif page == "Entreprises":
        page_companies()
    elif page == "Cartographie":
        page_map()
    elif page == "Statistiques":
        page_statistics()
    elif page == "Courriers":
        page_letters()
    elif page == "Paramètres":
        page_settings()


if __name__ == "__main__":
    main()
