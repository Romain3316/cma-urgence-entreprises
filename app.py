# ============================================================
# CMA URGENCE ENTREPRISES
# Version 1.0 - Prototype fonctionnel Streamlit
# ============================================================

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st


# ============================================================
# CONFIGURATION GÉNÉRALE
# ============================================================

st.set_page_config(
    page_title="CMA Urgence Entreprises",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_NAME = "CMA Urgence Entreprises"
APP_SUBTITLE = "Centre de pilotage et d’accompagnement des entreprises"

CMA_RED = "#C8102E"
CMA_RED_DARK = "#970B22"
TEXT_DARK = "#172033"
TEXT_MUTED = "#667085"
BACKGROUND = "#F3F5F8"
CARD_BACKGROUND = "#FFFFFF"
BORDER_COLOR = "#E5E9F0"

STATUS_COLORS = {
    "Critique": [200, 16, 46, 220],
    "À rappeler": [241, 145, 0, 220],
    "Accompagnement en cours": [38, 113, 221, 220],
    "Activité reprise": [22, 163, 74, 220],
    "Clôturé": [102, 112, 133, 220],
}

STATUS_HEX = {
    "Critique": "#C8102E",
    "À rappeler": "#F19100",
    "Accompagnement en cours": "#2671DD",
    "Activité reprise": "#16A34A",
    "Clôturé": "#667085",
}

URGENCE_LEVELS = ["Faible", "Modérée", "Élevée", "Critique"]

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


# ============================================================
# STYLE CSS
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

            .stApp {{
                background:
                    radial-gradient(
                        circle at top right,
                        rgba(200, 16, 46, 0.055),
                        transparent 28%
                    ),
                    var(--background);
            }}

            .main .block-container {{
                max-width: 1500px;
                padding-top: 1.4rem;
                padding-bottom: 3rem;
            }}

            [data-testid="stSidebar"] {{
                background:
                    linear-gradient(
                        180deg,
                        #111827 0%,
                        #182131 55%,
                        #111827 100%
                    );
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }}

            [data-testid="stSidebar"] * {{
                color: #FFFFFF;
            }}

            [data-testid="stSidebar"] .stRadio label {{
                padding: 0.45rem 0.35rem;
                border-radius: 10px;
                transition: all 0.18s ease;
            }}

            [data-testid="stSidebar"] .stRadio label:hover {{
                background: rgba(255, 255, 255, 0.08);
                transform: translateX(3px);
            }}

            [data-testid="stSidebar"] hr {{
                border-color: rgba(255, 255, 255, 0.12);
            }}

            .sidebar-brand {{
                padding: 0.65rem 0.2rem 1rem 0.2rem;
            }}

            .sidebar-brand-title {{
                font-size: 1.08rem;
                font-weight: 800;
                color: white;
                line-height: 1.2;
            }}

            .sidebar-brand-subtitle {{
                margin-top: 0.35rem;
                color: rgba(255, 255, 255, 0.62);
                font-size: 0.76rem;
                line-height: 1.35;
            }}

            .sidebar-red-line {{
                width: 42px;
                height: 4px;
                border-radius: 999px;
                background: var(--cma-red);
                margin-top: 0.85rem;
            }}

            .app-header {{
                position: relative;
                overflow: hidden;
                padding: 1.65rem 1.8rem;
                margin-bottom: 1.25rem;
                border-radius: 22px;
                background:
                    linear-gradient(
                        125deg,
                        #111827 0%,
                        #1F2937 60%,
                        #32131C 100%
                    );
                box-shadow: 0 16px 36px rgba(16, 24, 40, 0.14);
            }}

            .app-header::after {{
                content: "";
                position: absolute;
                top: -65px;
                right: -50px;
                width: 210px;
                height: 210px;
                border-radius: 50%;
                background: rgba(200, 16, 46, 0.24);
            }}

            .app-header-kicker {{
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                margin-bottom: 0.65rem;
                color: #FCA5B5;
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.11em;
                text-transform: uppercase;
            }}

            .app-header-title {{
                position: relative;
                z-index: 2;
                margin: 0;
                color: #FFFFFF;
                font-size: 2rem;
                font-weight: 850;
                letter-spacing: -0.035em;
            }}

            .app-header-subtitle {{
                position: relative;
                z-index: 2;
                max-width: 760px;
                margin-top: 0.55rem;
                color: rgba(255, 255, 255, 0.72);
                font-size: 0.94rem;
            }}

            .section-title {{
                margin-top: 0.35rem;
                margin-bottom: 0.15rem;
                color: var(--text);
                font-size: 1.2rem;
                font-weight: 800;
                letter-spacing: -0.02em;
            }}

            .section-subtitle {{
                margin-bottom: 1rem;
                color: var(--muted);
                font-size: 0.86rem;
            }}

            .kpi-card {{
                position: relative;
                min-height: 145px;
                overflow: hidden;
                padding: 1.15rem 1.2rem;
                border: 1px solid var(--border);
                border-radius: 18px;
                background: var(--card);
                box-shadow: 0 7px 22px rgba(16, 24, 40, 0.06);
                transition:
                    transform 0.18s ease,
                    box-shadow 0.18s ease;
            }}

            .kpi-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(16, 24, 40, 0.10);
            }}

            .kpi-icon {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: 42px;
                height: 42px;
                margin-bottom: 0.85rem;
                border-radius: 13px;
                font-size: 1.15rem;
            }}

            .kpi-label {{
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 700;
            }}

            .kpi-value {{
                margin-top: 0.18rem;
                color: var(--text);
                font-size: 2rem;
                font-weight: 850;
                line-height: 1;
                letter-spacing: -0.04em;
            }}

            .kpi-detail {{
                margin-top: 0.52rem;
                color: var(--muted);
                font-size: 0.72rem;
            }}

            .panel {{
                padding: 1.15rem 1.2rem;
                border: 1px solid var(--border);
                border-radius: 18px;
                background: var(--card);
                box-shadow: 0 7px 22px rgba(16, 24, 40, 0.055);
            }}

            .alert-card {{
                padding: 1rem;
                margin-bottom: 0.65rem;
                border: 1px solid #FED3DB;
                border-left: 5px solid var(--cma-red);
                border-radius: 14px;
                background: #FFF8F9;
            }}

            .alert-card-title {{
                color: #871126;
                font-size: 0.9rem;
                font-weight: 800;
            }}

            .alert-card-meta {{
                margin-top: 0.3rem;
                color: #7D5560;
                font-size: 0.75rem;
            }}

            .company-header {{
                padding: 1.25rem;
                border: 1px solid var(--border);
                border-radius: 18px;
                background: linear-gradient(145deg, #FFFFFF, #F9FAFB);
                box-shadow: 0 8px 24px rgba(16, 24, 40, 0.06);
            }}

            .company-name {{
                margin: 0;
                color: var(--text);
                font-size: 1.45rem;
                font-weight: 850;
            }}

            .company-meta {{
                margin-top: 0.4rem;
                color: var(--muted);
                font-size: 0.82rem;
            }}

            .status-pill {{
                display: inline-flex;
                align-items: center;
                padding: 0.32rem 0.7rem;
                border-radius: 999px;
                color: white;
                font-size: 0.72rem;
                font-weight: 800;
            }}

            .timeline-item {{
                position: relative;
                padding: 0 0 1.15rem 1.5rem;
                border-left: 2px solid #E5E7EB;
            }}

            .timeline-item::before {{
                content: "";
                position: absolute;
                top: 0.2rem;
                left: -0.42rem;
                width: 0.72rem;
                height: 0.72rem;
                border: 2px solid white;
                border-radius: 50%;
                background: var(--cma-red);
                box-shadow: 0 0 0 2px #F4B4C0;
            }}

            .timeline-date {{
                color: var(--cma-red);
                font-size: 0.72rem;
                font-weight: 800;
            }}

            .timeline-title {{
                margin-top: 0.12rem;
                color: var(--text);
                font-size: 0.88rem;
                font-weight: 750;
            }}

            .timeline-description {{
                margin-top: 0.18rem;
                color: var(--muted);
                font-size: 0.76rem;
            }}

            .empty-state {{
                padding: 2rem 1rem;
                border: 1px dashed #D5D9E2;
                border-radius: 16px;
                color: var(--muted);
                background: #FAFBFC;
                text-align: center;
            }}

            .footer-note {{
                margin-top: 2rem;
                padding-top: 1rem;
                border-top: 1px solid var(--border);
                color: var(--muted);
                font-size: 0.72rem;
                text-align: center;
            }}

            div[data-testid="stForm"] {{
                padding: 1.25rem;
                border: 1px solid var(--border);
                border-radius: 18px;
                background: white;
                box-shadow: 0 7px 22px rgba(16, 24, 40, 0.055);
            }}

            div[data-testid="stExpander"] {{
                border: 1px solid var(--border);
                border-radius: 14px;
                background: white;
            }}

            .stButton > button,
            .stDownloadButton > button {{
                min-height: 2.8rem;
                border-radius: 11px;
                font-weight: 750;
                transition: all 0.18s ease;
            }}

            .stButton > button:hover,
            .stDownloadButton > button:hover {{
                transform: translateY(-1px);
            }}

            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stNumberInput input {{
                border-radius: 10px;
            }}

            [data-testid="stDataFrame"] {{
                overflow: hidden;
                border: 1px solid var(--border);
                border-radius: 14px;
            }}

            @media (max-width: 900px) {{
                .app-header-title {{
                    font-size: 1.55rem;
                }}

                .kpi-card {{
                    min-height: 125px;
                }}
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
            "description": (
                "Atelier inaccessible. Matériel endommagé et activité totalement interrompue."
            ),
            "date_contact": now - timedelta(hours=3),
            "date_relance": date.today() + timedelta(days=1),
            "latitude": 44.8729,
            "longitude": -1.0926,
            "historique": [
                {
                    "date": now - timedelta(hours=3),
                    "titre": "Premier contact",
                    "description": "Diagnostic initial réalisé par téléphone.",
                },
                {
                    "date": now - timedelta(hours=2),
                    "titre": "Orientation assurance",
                    "description": "Transmission de la checklist des pièces justificatives.",
                },
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
            "description": (
                "Activité très réduite. Difficultés d’approvisionnement et baisse de fréquentation."
            ),
            "date_contact": now - timedelta(days=1, hours=2),
            "date_relance": date.today(),
            "latitude": 44.9028,
            "longitude": -0.9928,
            "historique": [
                {
                    "date": now - timedelta(days=1, hours=2),
                    "titre": "Premier contact",
                    "description": "Évaluation des impacts économiques et sociaux.",
                }
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
            "description": (
                "Établissement évacué temporairement. Nombreuses annulations et demandes de remboursement."
            ),
            "date_contact": now - timedelta(days=2),
            "date_relance": date.today() + timedelta(days=2),
            "latitude": 44.9772,
            "longitude": -1.0767,
            "historique": [
                {
                    "date": now - timedelta(days=2),
                    "titre": "Signalement",
                    "description": "Entreprise identifiée par la cellule territoriale.",
                },
                {
                    "date": now - timedelta(days=1),
                    "titre": "Accompagnement engagé",
                    "description": "Analyse des contrats et des pertes prévisionnelles.",
                },
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
            "description": (
                "Fermeture préventive de trois jours. L’activité a repris progressivement."
            ),
            "date_contact": now - timedelta(days=4),
            "date_relance": date.today() + timedelta(days=7),
            "latitude": 44.9665,
            "longitude": -0.8841,
            "historique": [
                {
                    "date": now - timedelta(days=4),
                    "titre": "Premier contact",
                    "description": "Fermeture temporaire signalée.",
                },
                {
                    "date": now - timedelta(days=1),
                    "titre": "Reprise d’activité",
                    "description": "Réouverture de l’atelier et reprise des chantiers.",
                },
            ],
        },
        {
            "id": 5,
            "siren": "412598763",
            "raison_sociale": "Évasion Cycles",
            "dirigeant": "Marc Lefèvre",
            "activite": "Commerce et réparation de cycles",
            "commune": "Carcans",
            "adresse": "22 avenue de Maubuisson",
            "telephone": "05 56 00 00 05",
            "email": "contact@evasioncycles.fr",
            "effectif": 2,
            "statut": "Clôturé",
            "urgence": "Faible",
            "conseiller": "Marlène",
            "besoins": "Information générale",
            "description": (
                "Pas de dégâts matériels. Baisse ponctuelle de fréquentation."
            ),
            "date_contact": now - timedelta(days=6),
            "date_relance": None,
            "latitude": 45.0786,
            "longitude": -1.0447,
            "historique": [
                {
                    "date": now - timedelta(days=6),
                    "titre": "Premier contact",
                    "description": "Évaluation rapide de la situation.",
                },
                {
                    "date": now - timedelta(days=3),
                    "titre": "Dossier clôturé",
                    "description": "Aucun accompagnement complémentaire demandé.",
                },
            ],
        },
        {
            "id": 6,
            "siren": "963258741",
            "raison_sociale": "La Cabane Gourmande",
            "dirigeant": "Élodie Roux",
            "activite": "Restauration",
            "commune": "Lège-Cap-Ferret",
            "adresse": "18 route du Cap",
            "telephone": "05 56 00 00 06",
            "email": "contact@cabane-gourmande.fr",
            "effectif": 8,
            "statut": "À rappeler",
            "urgence": "Modérée",
            "conseiller": "Nadia",
            "besoins": "Trésorerie, salariés",
            "description": (
                "Baisse importante de chiffre d’affaires liée aux restrictions d’accès."
            ),
            "date_contact": now - timedelta(hours=8),
            "date_relance": date.today(),
            "latitude": 44.7935,
            "longitude": -1.1460,
            "historique": [
                {
                    "date": now - timedelta(hours=8),
                    "titre": "Premier contact",
                    "description": "Demande de rappel après échange avec l’expert-comptable.",
                }
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

    if "cellule_name" not in st.session_state:
        st.session_state.cellule_name = "Cellule de crise Gironde"

    if "current_advisor" not in st.session_state:
        st.session_state.current_advisor = "Romain"


# ============================================================
# OUTILS
# ============================================================

def companies_dataframe() -> pd.DataFrame:
    rows = []

    for company in st.session_state.companies:
        rows.append(
            {
                "ID": company["id"],
                "SIREN": company["siren"],
                "Entreprise": company["raison_sociale"],
                "Activité": company["activite"],
                "Commune": company["commune"],
                "Statut": company["statut"],
                "Urgence": company["urgence"],
                "Conseiller": company["conseiller"],
                "Dernier contact": company["date_contact"],
                "Relance": company["date_relance"],
                "Latitude": company["latitude"],
                "Longitude": company["longitude"],
            }
        )

    return pd.DataFrame(rows)


def get_company(company_id: int) -> dict[str, Any] | None:
    for company in st.session_state.companies:
        if company["id"] == company_id:
            return company
    return None


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "Non renseigné"
    return value.strftime("%d/%m/%Y à %H:%M")


def format_date(value: date | None) -> str:
    if value is None:
        return "Aucune"
    return value.strftime("%d/%m/%Y")


def calculate_urgency_score(
    interruption: str,
    degats: str,
    tresorerie: str,
    salaries: str,
    accessibilite: str,
) -> tuple[int, str]:
    score = 0

    score += {
        "Aucune": 0,
        "Partielle": 2,
        "Totale": 4,
    }.get(interruption, 0)

    score += {
        "Aucun": 0,
        "Légers": 1,
        "Importants": 3,
        "Destruction majeure": 5,
    }.get(degats, 0)

    score += {
        "Pas de difficulté immédiate": 0,
        "Tension dans le mois": 2,
        "Risque sous 15 jours": 4,
        "Situation immédiate critique": 5,
    }.get(tresorerie, 0)

    score += {
        "Non concerné": 0,
        "Organisation maintenue": 1,
        "Activité partielle envisagée": 3,
        "Emplois directement menacés": 5,
    }.get(salaries, 0)

    score += {
        "Accessible": 0,
        "Accès limité": 2,
        "Zone inaccessible": 4,
    }.get(accessibilite, 0)

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
    return {
        "Critique": "Critique",
        "Élevée": "Accompagnement en cours",
        "Modérée": "À rappeler",
        "Faible": "Accompagnement en cours",
    }.get(level, "Accompagnement en cours")


def build_map_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    map_df = df.copy()

    map_df["Couleur"] = map_df["Statut"].map(STATUS_COLORS)
    map_df["Rayon"] = map_df["Urgence"].map(
        {
            "Faible": 170,
            "Modérée": 230,
            "Élevée": 300,
            "Critique": 380,
        }
    )

    return map_df


def render_map(
    df: pd.DataFrame,
    height: int = 480,
    zoom: float = 8.7,
) -> None:
    if df.empty:
        st.markdown(
            """
            <div class="empty-state">
                Aucun point ne correspond aux filtres sélectionnés.
            </div>
            """,
            unsafe_allow_html=True,
        )
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
        map_style="light",
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=zoom,
            pitch=0,
        ),
        layers=[layer],
        tooltip={
            "html": """
                <div style="
                    min-width: 220px;
                    font-family: Arial, sans-serif;
                ">
                    <div style="
                        font-size: 15px;
                        font-weight: 800;
                        margin-bottom: 7px;
                    ">
                        {Entreprise}
                    </div>
                    <div><b>Commune :</b> {Commune}</div>
                    <div><b>Activité :</b> {Activité}</div>
                    <div><b>Statut :</b> {Statut}</div>
                    <div><b>Urgence :</b> {Urgence}</div>
                    <div><b>Conseiller :</b> {Conseiller}</div>
                </div>
            """,
            "style": {
                "backgroundColor": "#111827",
                "color": "white",
                "borderRadius": "12px",
                "padding": "12px",
            },
        },
    )

    st.pydeck_chart(
        deck,
        height=height,
        use_container_width=True,
    )


def render_header(
    title: str,
    subtitle: str,
    kicker: str = "Cellule de crise",
) -> None:
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
    st.markdown(
        f"""
        <div class="section-title">{title}</div>
        <div class="section-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(
    label: str,
    value: int | str,
    icon: str,
    detail: str,
    background_color: str,
    icon_color: str,
) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div
                class="kpi-icon"
                style="
                    background:{background_color};
                    color:{icon_color};
                "
            >
                {icon}
            </div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_legend() -> None:
    legend_html = ""

    for status, color in STATUS_HEX.items():
        legend_html += (
            f'<span style="display:inline-flex;align-items:center;'
            f'margin-right:14px;margin-bottom:6px;font-size:12px;'
            f'color:#667085;">'
            f'<span style="width:9px;height:9px;border-radius:50%;'
            f'background:{color};margin-right:5px;"></span>{status}'
            f"</span>"
        )

    st.markdown(legend_html, unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(
        """
        <div class="footer-note">
            CMA Urgence Entreprises · Prototype V1.0 ·
            Données de démonstration non persistantes
        </div>
        """,
        unsafe_allow_html=True,
    )


def navigate_to(page: str, company_id: int | None = None) -> None:
    st.session_state.current_page = page

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
                <div class="sidebar-brand-title">
                    🚨 CMA Urgence<br>Entreprises
                </div>
                <div class="sidebar-brand-subtitle">
                    Pilotage et accompagnement des entreprises
                    impactées par une situation de crise.
                </div>
                <div class="sidebar-red-line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("NAVIGATION")

        pages = [
            "Tableau de bord",
            "Nouveau diagnostic",
            "Entreprises",
            "Cartographie",
            "Statistiques",
            "Courriers",
            "Paramètres",
        ]

        icons = {
            "Tableau de bord": "🏠",
            "Nouveau diagnostic": "➕",
            "Entreprises": "🏢",
            "Cartographie": "🗺️",
            "Statistiques": "📊",
            "Courriers": "📄",
            "Paramètres": "⚙️",
        }

        current_page = st.session_state.current_page

        if current_page not in pages:
            current_page = "Tableau de bord"

        page = st.radio(
            "Navigation",
            pages,
            index=pages.index(current_page),
            format_func=lambda item: f"{icons[item]}  {item}",
            label_visibility="collapsed",
        )

        st.session_state.current_page = page

        st.divider()

        st.caption("CELLULE ACTIVE")

        st.markdown(
            f"""
            <div style="
                padding:0.85rem;
                border:1px solid rgba(255,255,255,0.12);
                border-radius:13px;
                background:rgba(255,255,255,0.055);
            ">
                <div style="
                    font-size:0.73rem;
                    color:rgba(255,255,255,0.58);
                ">
                    Dispositif
                </div>
                <div style="
                    margin-top:0.18rem;
                    font-size:0.88rem;
                    font-weight:800;
                ">
                    {st.session_state.cellule_name}
                </div>
                <div style="
                    margin-top:0.7rem;
                    font-size:0.73rem;
                    color:rgba(255,255,255,0.58);
                ">
                    Conseiller
                </div>
                <div style="
                    margin-top:0.18rem;
                    font-size:0.84rem;
                    font-weight:700;
                ">
                    👤 {st.session_state.current_advisor}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Prototype local : les dossiers ne sont pas encore "
            "partagés entre les conseillers."
        )

    return page


# ============================================================
# PAGE : TABLEAU DE BORD
# ============================================================

def page_dashboard() -> None:
    render_header(
        APP_NAME,
        (
            "Vue consolidée de la situation, des entreprises suivies "
            "et des actions prioritaires."
        ),
        "Centre de commandement",
    )

    df = companies_dataframe()

    total = len(df)
    critiques = int((df["Statut"] == "Critique").sum())
    relances = int(
        df["Relance"].apply(
            lambda value: value is not None and value <= date.today()
        ).sum()
    )
    reprises = int(
        df["Statut"].isin(["Activité reprise", "Clôturé"]).sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi(
            "Entreprises suivies",
            total,
            "🏢",
            "Dossiers enregistrés dans la cellule",
            "#EEF4FF",
            "#2671DD",
        )

    with col2:
        render_kpi(
            "Relances à effectuer",
            relances,
            "☎️",
            "Échéance atteinte ou dépassée",
            "#FFF5E6",
            "#D97800",
        )

    with col3:
        render_kpi(
            "Situations critiques",
            critiques,
            "🚨",
            "Intervention prioritaire recommandée",
            "#FFF0F3",
            CMA_RED,
        )

    with col4:
        render_kpi(
            "Reprises ou clôtures",
            reprises,
            "✅",
            "Évolution favorable de la situation",
            "#ECFDF3",
            "#168A47",
        )

    st.write("")

    map_column, alerts_column = st.columns([2.25, 1], gap="large")

    with map_column:
        render_section_title(
            "Cartographie opérationnelle",
            "Position et niveau de priorité des entreprises accompagnées.",
        )

        render_status_legend()
        render_map(df, height=485)

    with alerts_column:
        render_section_title(
            "Situations prioritaires",
            "Dossiers nécessitant une attention rapide.",
        )

        priority_df = df[
            df["Statut"].isin(["Critique", "À rappeler"])
        ].sort_values(
            by=["Urgence", "Dernier contact"],
            ascending=[True, False],
        )

        if priority_df.empty:
            st.success("Aucune situation prioritaire actuellement.")

        for _, row in priority_df.head(5).iterrows():
            st.markdown(
                f"""
                <div class="alert-card">
                    <div class="alert-card-title">
                        {row["Entreprise"]}
                    </div>
                    <div class="alert-card-meta">
                        📍 {row["Commune"]}<br>
                        🚨 {row["Urgence"]} · {row["Statut"]}<br>
                        👤 {row["Conseiller"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Ouvrir le dossier",
                key=f"dashboard_open_{row['ID']}",
                use_container_width=True,
            ):
                navigate_to("Entreprises", int(row["ID"]))

    st.write("")

    left_chart, right_chart = st.columns([1.25, 1], gap="large")

    with left_chart:
        render_section_title(
            "Entreprises par commune",
            "Répartition territoriale des dossiers enregistrés.",
        )

        commune_df = (
            df.groupby("Commune")
            .size()
            .reset_index(name="Entreprises")
            .sort_values("Entreprises", ascending=True)
        )

        fig_communes = px.bar(
            commune_df,
            x="Entreprises",
            y="Commune",
            orientation="h",
            text="Entreprises",
        )

        fig_communes.update_traces(
            marker_color=CMA_RED,
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x} entreprise(s)<extra></extra>",
        )

        fig_communes.update_layout(
            height=355,
            margin=dict(l=5, r=25, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="",
            showlegend=False,
        )

        fig_communes.update_xaxes(
            showgrid=True,
            gridcolor="#EEF0F4",
            zeroline=False,
        )

        fig_communes.update_yaxes(showgrid=False)

        st.plotly_chart(
            fig_communes,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with right_chart:
        render_section_title(
            "Répartition par statut",
            "État actuel des accompagnements.",
        )

        status_df = (
            df.groupby("Statut")
            .size()
            .reset_index(name="Entreprises")
        )

        fig_status = px.donut(
            status_df,
            names="Statut",
            values="Entreprises",
            hole=0.67,
            color="Statut",
            color_discrete_map=STATUS_HEX,
        )

        fig_status.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{value} entreprise(s)<br>"
                "%{percent}<extra></extra>"
            ),
        )

        fig_status.update_layout(
            height=355,
            margin=dict(l=5, r=5, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
            ),
        )

        st.plotly_chart(
            fig_status,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    render_footer()


# ============================================================
# PAGE : NOUVEAU DIAGNOSTIC
# ============================================================

def page_diagnostic() -> None:
    render_header(
        "Nouveau diagnostic",
        (
            "Qualifier la situation de l’entreprise, identifier les "
            "priorités et préparer le plan d’action."
        ),
        "Accompagnement",
    )

    st.info(
        "Le diagnostic calcule automatiquement un niveau d’urgence. "
        "Le résultat reste modifiable par le conseiller."
    )

    with st.form("diagnostic_form", clear_on_submit=False):
        render_section_title(
            "1. Identification de l’entreprise",
            "Renseignez les informations principales du dossier.",
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            raison_sociale = st.text_input(
                "Raison sociale *",
                placeholder="Ex. Boulangerie des Pins",
            )

            siren = st.text_input(
                "SIREN",
                max_chars=9,
                placeholder="9 chiffres",
            )

            dirigeant = st.text_input(
                "Dirigeant",
                placeholder="Nom et prénom",
            )

        with col2:
            activite = st.text_input(
                "Activité *",
                placeholder="Ex. Boulangerie-pâtisserie",
            )

            commune = st.selectbox(
                "Commune *",
                list(COMMUNES_COORDONNEES.keys()),
            )

            adresse = st.text_input(
                "Adresse",
                placeholder="Adresse de l’établissement",
            )

        with col3:
            telephone = st.text_input(
                "Téléphone",
                placeholder="05 XX XX XX XX",
            )

            email = st.text_input(
                "E-mail",
                placeholder="contact@entreprise.fr",
            )

            effectif = st.number_input(
                "Effectif",
                min_value=0,
                max_value=999,
                value=1,
                step=1,
            )

        st.divider()

        render_section_title(
            "2. Évaluation des impacts",
            "Les réponses permettent d’estimer le niveau de priorité.",
        )

        col1, col2 = st.columns(2)

        with col1:
            interruption = st.radio(
                "Interruption d’activité",
                ["Aucune", "Partielle", "Totale"],
                horizontal=True,
            )

            degats = st.select_slider(
                "Dégâts matériels",
                options=[
                    "Aucun",
                    "Légers",
                    "Importants",
                    "Destruction majeure",
                ],
                value="Légers",
            )

            accessibilite = st.radio(
                "Accessibilité de l’établissement",
                ["Accessible", "Accès limité", "Zone inaccessible"],
            )

        with col2:
            tresorerie = st.selectbox(
                "Situation de trésorerie",
                [
                    "Pas de difficulté immédiate",
                    "Tension dans le mois",
                    "Risque sous 15 jours",
                    "Situation immédiate critique",
                ],
            )

            salaries = st.selectbox(
                "Situation des salariés",
                [
                    "Non concerné",
                    "Organisation maintenue",
                    "Activité partielle envisagée",
                    "Emplois directement menacés",
                ],
            )

            date_relance = st.date_input(
                "Date de relance souhaitée",
                value=date.today() + timedelta(days=2),
            )

        st.divider()

        render_section_title(
            "3. Besoins et compte rendu",
            "Décrivez la situation avec les mots de l’entreprise.",
        )

        besoins_selectionnes = st.multiselect(
            "Besoins identifiés",
            [
                "Assurance",
                "Trésorerie",
                "Banque",
                "URSSAF",
                "DGFIP",
                "Activité partielle",
                "Salariés",
                "Fournisseurs",
                "Clients",
                "Relogement de l’activité",
                "Reprise d’activité",
                "Communication",
                "Soutien psychologique",
                "Autre",
            ],
        )

        description = st.text_area(
            "Description de la situation *",
            height=150,
            placeholder=(
                "Décrivez les dégâts, l’interruption d’activité, les "
                "démarches déjà engagées et les principales difficultés."
            ),
        )

        conseiller = st.text_input(
            "Conseiller en charge",
            value=st.session_state.current_advisor,
        )

        submitted = st.form_submit_button(
            "Enregistrer le diagnostic",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not raison_sociale.strip():
            st.error("La raison sociale est obligatoire.")
            return

        if not activite.strip():
            st.error("L’activité est obligatoire.")
            return

        if not description.strip():
            st.error("La description de la situation est obligatoire.")
            return

        if siren and (not siren.isdigit() or len(siren) != 9):
            st.error("Le SIREN doit contenir exactement 9 chiffres.")
            return

        duplicate = None

        if siren:
            duplicate = next(
                (
                    company
                    for company in st.session_state.companies
                    if company["siren"] == siren
                ),
                None,
            )

        if duplicate:
            st.warning(
                "Une entreprise possédant ce SIREN existe déjà : "
                f"{duplicate['raison_sociale']}."
            )
            return

        score, urgence_calculee = calculate_urgency_score(
            interruption,
            degats,
            tresorerie,
            salaries,
            accessibilite,
        )

        latitude, longitude = COMMUNES_COORDONNEES[commune]

        new_id = max(
            company["id"]
            for company in st.session_state.companies
        ) + 1

        needs_text = (
            ", ".join(besoins_selectionnes)
            if besoins_selectionnes
            else "À préciser"
        )

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
            "statut": urgency_to_status(urgence_calculee),
            "urgence": urgence_calculee,
            "conseiller": conseiller.strip() or "Non attribué",
            "besoins": needs_text,
            "description": description.strip(),
            "date_contact": datetime.now(),
            "date_relance": date_relance,
            "latitude": latitude,
            "longitude": longitude,
            "historique": [
                {
                    "date": datetime.now(),
                    "titre": "Diagnostic initial",
                    "description": (
                        f"Diagnostic enregistré. Score d’urgence : "
                        f"{score}/23."
                    ),
                }
            ],
        }

        st.session_state.companies.append(company)
        st.session_state.selected_company_id = new_id

        st.success(
            f"Diagnostic enregistré : niveau d’urgence "
            f"« {urgence_calculee} » — score {score}/23."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Ouvrir le dossier",
                type="primary",
                use_container_width=True,
            ):
                navigate_to("Entreprises", new_id)

        with col2:
            if st.button(
                "Voir la cartographie",
                use_container_width=True,
            ):
                navigate_to("Cartographie")


# ============================================================
# PAGE : ENTREPRISES
# ============================================================

def page_companies() -> None:
    render_header(
        "Entreprises accompagnées",
        (
            "Consulter, filtrer et mettre à jour les dossiers suivis "
            "par la cellule de crise."
        ),
        "Portefeuille",
    )

    df = companies_dataframe()

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        search = st.text_input(
            "Rechercher",
            placeholder="Entreprise, SIREN, commune...",
        )

    with filter_col2:
        status_filter = st.multiselect(
            "Statut",
            options=list(STATUS_COLORS.keys()),
        )

    with filter_col3:
        commune_filter = st.multiselect(
            "Commune",
            options=sorted(df["Commune"].unique()),
        )

    with filter_col4:
        advisor_filter = st.multiselect(
            "Conseiller",
            options=sorted(df["Conseiller"].unique()),
        )

    filtered_df = df.copy()

    if search:
        normalized_search = search.casefold()

        mask = (
            filtered_df["Entreprise"]
            .str.casefold()
            .str.contains(normalized_search, na=False)
            |
            filtered_df["SIREN"]
            .astype(str)
            .str.casefold()
            .str.contains(normalized_search, na=False)
            |
            filtered_df["Commune"]
            .str.casefold()
            .str.contains(normalized_search, na=False)
            |
            filtered_df["Activité"]
            .str.casefold()
            .str.contains(normalized_search, na=False)
        )

        filtered_df = filtered_df[mask]

    if status_filter:
        filtered_df = filtered_df[
            filtered_df["Statut"].isin(status_filter)
        ]

    if commune_filter:
        filtered_df = filtered_df[
            filtered_df["Commune"].isin(commune_filter)
        ]

    if advisor_filter:
        filtered_df = filtered_df[
            filtered_df["Conseiller"].isin(advisor_filter)
        ]

    render_section_title(
        f"Résultats — {len(filtered_df)} entreprise(s)",
        "Sélectionnez une entreprise pour consulter sa fiche complète.",
    )

    display_df = filtered_df[
        [
            "Entreprise",
            "SIREN",
            "Commune",
            "Activité",
            "Statut",
            "Urgence",
            "Conseiller",
            "Dernier contact",
            "Relance",
        ]
    ].copy()

    display_df["Dernier contact"] = display_df[
        "Dernier contact"
    ].dt.strftime("%d/%m/%Y %H:%M")

    display_df["Relance"] = display_df["Relance"].apply(format_date)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=330,
        column_config={
            "Entreprise": st.column_config.TextColumn(
                "Entreprise",
                width="large",
            ),
            "Statut": st.column_config.TextColumn(
                "Statut",
                width="medium",
            ),
            "Urgence": st.column_config.TextColumn(
                "Urgence",
                width="small",
            ),
        },
    )

    if filtered_df.empty:
        return

    company_options = {
        f"{row['Entreprise']} — {row['Commune']}": int(row["ID"])
        for _, row in filtered_df.iterrows()
    }

    selected_id = st.session_state.selected_company_id

    selected_label = next(
        (
            label
            for label, company_id in company_options.items()
            if company_id == selected_id
        ),
        next(iter(company_options)),
    )

    selected_label = st.selectbox(
        "Ouvrir une fiche entreprise",
        options=list(company_options.keys()),
        index=list(company_options.keys()).index(selected_label),
    )

    selected_id = company_options[selected_label]
    st.session_state.selected_company_id = selected_id

    company = get_company(selected_id)

    if not company:
        st.error("Entreprise introuvable.")
        return

    render_company_record(company)


def render_company_record(company: dict[str, Any]) -> None:
    status_color = STATUS_HEX.get(company["statut"], "#667085")

    st.markdown(
        f"""
        <div class="company-header">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:flex-start;
                gap:1rem;
                flex-wrap:wrap;
            ">
                <div>
                    <h2 class="company-name">
                        {company["raison_sociale"]}
                    </h2>
                    <div class="company-meta">
                        {company["activite"]} · {company["commune"]} ·
                        SIREN {company["siren"]}
                    </div>
                </div>
                <span
                    class="status-pill"
                    style="background:{status_color};"
                >
                    {company["statut"]}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    info_col, action_col = st.columns([1.45, 1], gap="large")

    with info_col:
        render_section_title(
            "Informations",
            "Coordonnées et situation actuelle.",
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                **Dirigeant**  
                {company["dirigeant"]}

                **Téléphone**  
                {company["telephone"]}

                **E-mail**  
                {company["email"]}

                **Adresse**  
                {company["adresse"]}, {company["commune"]}
                """
            )

        with col2:
            st.markdown(
                f"""
                **Effectif**  
                {company["effectif"]}

                **Niveau d’urgence**  
                {company["urgence"]}

                **Conseiller**  
                {company["conseiller"]}

                **Prochaine relance**  
                {format_date(company["date_relance"])}
                """
            )

        st.markdown("**Besoins identifiés**")
        st.write(company["besoins"])

        st.markdown("**Synthèse de la situation**")
        st.write(company["description"])

    with action_col:
        render_section_title(
            "Mise à jour rapide",
            "Modifier le statut ou ajouter une action.",
        )

        with st.form(f"update_company_{company['id']}"):
            new_status = st.selectbox(
                "Statut",
                list(STATUS_COLORS.keys()),
                index=list(STATUS_COLORS.keys()).index(
                    company["statut"]
                ),
            )

            new_urgency = st.selectbox(
                "Urgence",
                URGENCE_LEVELS,
                index=URGENCE_LEVELS.index(company["urgence"]),
            )

            new_follow_up = st.date_input(
                "Prochaine relance",
                value=(
                    company["date_relance"]
                    if company["date_relance"]
                    else date.today() + timedelta(days=3)
                ),
            )

            action_title = st.text_input(
                "Action réalisée",
                placeholder="Ex. Échange avec l’assurance",
            )

            action_description = st.text_area(
                "Commentaire",
                placeholder="Précisez le résultat de l’action.",
                height=90,
            )

            update_submitted = st.form_submit_button(
                "Enregistrer la mise à jour",
                type="primary",
                use_container_width=True,
            )

        if update_submitted:
            company["statut"] = new_status
            company["urgence"] = new_urgency
            company["date_relance"] = new_follow_up
            company["date_contact"] = datetime.now()

            if action_title.strip():
                company["historique"].insert(
                    0,
                    {
                        "date": datetime.now(),
                        "titre": action_title.strip(),
                        "description": (
                            action_description.strip()
                            or "Aucun commentaire complémentaire."
                        ),
                    },
                )

            st.success("Le dossier a été mis à jour.")
            st.rerun()

    st.write("")
    render_section_title(
        "Historique du dossier",
        "Chronologie des contacts et des démarches.",
    )

    history = sorted(
        company["historique"],
        key=lambda item: item["date"],
        reverse=True,
    )

    for item in history:
        st.markdown(
            f"""
            <div class="timeline-item">
                <div class="timeline-date">
                    {format_datetime(item["date"])}
                </div>
                <div class="timeline-title">
                    {item["titre"]}
                </div>
                <div class="timeline-description">
                    {item["description"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# PAGE : CARTOGRAPHIE
# ============================================================

def page_map() -> None:
    render_header(
        "Cartographie collaborative",
        (
            "Visualiser la répartition territoriale des entreprises, "
            "leur statut et leur niveau d’urgence."
        ),
        "Pilotage territorial",
    )

    df = companies_dataframe()

    col1, col2, col3 = st.columns(3)

    with col1:
        statuses = st.multiselect(
            "Statuts",
            options=list(STATUS_COLORS.keys()),
            default=list(STATUS_COLORS.keys()),
        )

    with col2:
        urgencies = st.multiselect(
            "Niveaux d’urgence",
            options=URGENCE_LEVELS,
            default=URGENCE_LEVELS,
        )

    with col3:
        advisors = st.multiselect(
            "Conseillers",
            options=sorted(df["Conseiller"].unique()),
            default=sorted(df["Conseiller"].unique()),
        )

    filtered_df = df[
        df["Statut"].isin(statuses)
        & df["Urgence"].isin(urgencies)
        & df["Conseiller"].isin(advisors)
    ]

    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        st.metric("Points affichés", len(filtered_df))

    with kpi2:
        st.metric(
            "Communes concernées",
            filtered_df["Commune"].nunique(),
        )

    with kpi3:
        st.metric(
            "Effectifs concernés",
            int(
                sum(
                    get_company(int(company_id))["effectif"]
                    for company_id in filtered_df["ID"]
                    if get_company(int(company_id))
                )
            ),
        )

    render_status_legend()
    render_map(filtered_df, height=650, zoom=8.7)

    st.caption(
        "Survolez un point pour afficher le résumé de l’entreprise."
    )


# ============================================================
# PAGE : STATISTIQUES
# ============================================================

def page_statistics() -> None:
    render_header(
        "Statistiques",
        (
            "Analyser l’activité de la cellule et les caractéristiques "
            "des entreprises accompagnées."
        ),
        "Analyse",
    )

    df = companies_dataframe()

    company_details = pd.DataFrame(st.session_state.companies)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_section_title(
            "Entreprises par niveau d’urgence",
            "Nombre de dossiers selon leur degré de priorité.",
        )

        urgency_order = ["Faible", "Modérée", "Élevée", "Critique"]

        urgency_df = (
            df.groupby("Urgence")
            .size()
            .reindex(urgency_order, fill_value=0)
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
            margin=dict(l=5, r=5, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="",
        )

        fig.update_yaxes(
            gridcolor="#EEF0F4",
            zeroline=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with col2:
        render_section_title(
            "Effectifs concernés par activité",
            "Somme des emplois liés aux entreprises suivies.",
        )

        activity_df = (
            company_details.groupby("activite")["effectif"]
            .sum()
            .reset_index()
            .sort_values("effectif", ascending=True)
        )

        fig = px.bar(
            activity_df,
            x="effectif",
            y="activite",
            orientation="h",
            text="effectif",
        )

        fig.update_traces(marker_color="#2671DD")

        fig.update_layout(
            height=370,
            showlegend=False,
            margin=dict(l=5, r=25, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="",
        )

        fig.update_xaxes(
            gridcolor="#EEF0F4",
            zeroline=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.write("")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_section_title(
            "Charge par conseiller",
            "Nombre de dossiers actuellement attribués.",
        )

        advisor_df = (
            df.groupby("Conseiller")
            .size()
            .reset_index(name="Dossiers")
            .sort_values("Dossiers", ascending=False)
        )

        fig = px.bar(
            advisor_df,
            x="Conseiller",
            y="Dossiers",
            text="Dossiers",
        )

        fig.update_traces(marker_color=CMA_RED)

        fig.update_layout(
            height=340,
            margin=dict(l=5, r=5, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="",
        )

        fig.update_yaxes(
            gridcolor="#EEF0F4",
            zeroline=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with col2:
        render_section_title(
            "Principaux besoins identifiés",
            "Fréquence des besoins renseignés dans les dossiers.",
        )

        all_needs: list[str] = []

        for needs in company_details["besoins"].fillna(""):
            all_needs.extend(
                [
                    need.strip()
                    for need in str(needs).split(",")
                    if need.strip()
                ]
            )

        needs_df = (
            pd.Series(all_needs, name="Besoin")
            .value_counts()
            .reset_index()
        )

        needs_df.columns = ["Besoin", "Occurrences"]
        needs_df = needs_df.head(8).sort_values(
            "Occurrences",
            ascending=True,
        )

        fig = px.bar(
            needs_df,
            x="Occurrences",
            y="Besoin",
            orientation="h",
            text="Occurrences",
        )

        fig.update_traces(marker_color="#475467")

        fig.update_layout(
            height=340,
            margin=dict(l=5, r=25, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="",
        )

        fig.update_xaxes(
            gridcolor="#EEF0F4",
            zeroline=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )


# ============================================================
# PAGE : COURRIERS
# ============================================================

def build_letter(
    company: dict[str, Any],
    recipient_type: str,
    subject: str,
    request: str,
    advisor_name: str,
) -> str:
    today = date.today().strftime("%d/%m/%Y")

    recipients = {
        "Assurance": "Service sinistres",
        "Banque": "Direction de l’agence bancaire",
        "URSSAF": "Service des entreprises en difficulté",
        "DGFIP": "Service des impôts des entreprises",
        "Bailleur": "Propriétaire / bailleur des locaux",
        "Fournisseur": "Service comptable du fournisseur",
    }

    recipient = recipients.get(recipient_type, recipient_type)

    return f"""\
{company["raison_sociale"]}
{company["adresse"]}
{company["commune"]}

À l’attention de :
{recipient}

Le {today}

Objet : {subject}

Madame, Monsieur,

L’entreprise {company["raison_sociale"]}, exerçant une activité de \
{company["activite"]} à {company["commune"]}, rencontre actuellement \
des difficultés importantes à la suite de la situation de crise ayant \
affecté son territoire.

La situation constatée est la suivante :

{company["description"]}

Les principaux besoins identifiés sont :

{company["besoins"]}

Dans ce contexte, nous sollicitons votre bienveillance afin d’étudier \
la demande suivante :

{request}

L’entreprise reste disponible pour transmettre tout document \
justificatif nécessaire à l’étude de sa situation.

Nous vous remercions par avance pour l’attention portée à cette \
demande et pour votre retour dans les meilleurs délais.

Veuillez agréer, Madame, Monsieur, l’expression de nos salutations \
distinguées.

{company["dirigeant"]}
Pour {company["raison_sociale"]}

Courrier préparé avec l’appui de :
{advisor_name}
CMA Nouvelle-Aquitaine
"""


def page_letters() -> None:
    render_header(
        "Générateur de courriers",
        (
            "Préparer rapidement un courrier personnalisé à partir "
            "des informations du dossier entreprise."
        ),
        "Documents",
    )

    companies = st.session_state.companies

    company_options = {
        f"{company['raison_sociale']} — {company['commune']}": company["id"]
        for company in companies
    }

    selected_label = st.selectbox(
        "Entreprise",
        options=list(company_options.keys()),
    )

    company = get_company(company_options[selected_label])

    if not company:
        st.error("Entreprise introuvable.")
        return

    col1, col2 = st.columns([1, 1.35], gap="large")

    with col1:
        recipient_type = st.selectbox(
            "Destinataire",
            [
                "Assurance",
                "Banque",
                "URSSAF",
                "DGFIP",
                "Bailleur",
                "Fournisseur",
                "Autre",
            ],
        )

        subject = st.text_input(
            "Objet du courrier",
            value="Demande d’examen bienveillant de la situation",
        )

        request = st.text_area(
            "Demande formulée",
            value=(
                "Nous demandons l’examen des solutions mobilisables, "
                "notamment la mise en place d’un délai, d’un report ou "
                "d’un accompagnement adapté à la situation de "
                "l’entreprise."
            ),
            height=170,
        )

        advisor_name = st.text_input(
            "Conseiller",
            value=st.session_state.current_advisor,
        )

    letter = build_letter(
        company,
        recipient_type,
        subject,
        request,
        advisor_name,
    )

    with col2:
        st.text_area(
            "Aperçu du courrier",
            value=letter,
            height=570,
        )

        st.download_button(
            "Télécharger le courrier au format texte",
            data=letter.encode("utf-8"),
            file_name=(
                f"courrier_{company['raison_sociale']}"
                .replace(" ", "_")
                .lower()
                + ".txt"
            ),
            mime="text/plain",
            type="primary",
            use_container_width=True,
        )

    st.warning(
        "Le courrier doit être relu, complété et validé par le "
        "conseiller avant envoi."
    )


# ============================================================
# PAGE : PARAMÈTRES
# ============================================================

def page_settings() -> None:
    render_header(
        "Paramètres",
        (
            "Configurer les informations générales de la cellule "
            "et l’utilisateur courant."
        ),
        "Administration",
    )

    with st.form("settings_form"):
        cellule_name = st.text_input(
            "Nom de la cellule",
            value=st.session_state.cellule_name,
        )

        current_advisor = st.text_input(
            "Nom du conseiller courant",
            value=st.session_state.current_advisor,
        )

        save_settings = st.form_submit_button(
            "Enregistrer les paramètres",
            type="primary",
        )

    if save_settings:
        st.session_state.cellule_name = (
            cellule_name.strip() or "Cellule de crise"
        )

        st.session_state.current_advisor = (
            current_advisor.strip() or "Conseiller CMA"
        )

        st.success("Paramètres enregistrés.")
        st.rerun()

    st.divider()

    render_section_title(
        "Données de démonstration",
        (
            "Réinitialiser l’application efface les diagnostics ajoutés "
            "pendant cette session."
        ),
    )

    if st.button(
        "Réinitialiser les données de démonstration",
        use_container_width=False,
    ):
        st.session_state.companies = get_demo_companies()
        st.session_state.selected_company_id = 1
        st.success("Les données de démonstration ont été réinitialisées.")
        st.rerun()

    st.divider()

    st.info(
        "Cette version utilise uniquement la mémoire de la session "
        "Streamlit. Une future version connectée à une base PostgreSQL "
        "ou Supabase permettra le partage des dossiers et de la carte "
        "entre les conseillers."
    )


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
