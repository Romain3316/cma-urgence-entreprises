from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
import html
import re
import unicodedata

import pandas as pd
import plotly.express as px
import pydeck as pdk
import requests
import streamlit as st
from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
from staticmap import CircleMarker, StaticMap
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CMA — Rapport cellule de crise",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "CMA — Cartographie cellule de crise"
CMA_RED = "#D71920"
CMA_RED_DARK = "#A20F18"
TEXT_DARK = "#172033"
TEXT_MUTED = "#667085"
BACKGROUND = "#F4F6F8"
CARD_BACKGROUND = "#FFFFFF"
BORDER_COLOR = "#E3E7ED"

GEOCODING_URL = "https://data.geopf.fr/geocodage/search"
CMA_LOGO_PATH = "logo_cma_na_gironde.png"

CONTACT_STATES = [
    "Entreprise contactée",
    "Message vocal & mail envoyé",
    "Mauvais numéro",
    "Déjà contactée",
    "À rappeler",
    "Non renseigné",
]

CONTACT_STATE_COLORS = {
    "Entreprise contactée": [22, 163, 74, 225],
    "Message vocal & mail envoyé": [6, 182, 212, 225],
    "Mauvais numéro": [185, 28, 28, 225],
    "Déjà contactée": [234, 88, 12, 225],
    "À rappeler": [241, 145, 0, 225],
    "Non renseigné": [102, 112, 133, 225],
}

CONTACT_STATE_HEX = {
    key: "#{:02X}{:02X}{:02X}".format(*value[:3])
    for key, value in CONTACT_STATE_COLORS.items()
}

FINAL_CONTACT_STATES = {
    "Entreprise contactée",
    "Mauvais numéro",
    "Déjà contactée",
}

IMPORT_COLUMNS = [
    "Nom de l'entreprise",
    "Adresse",
    "Commune",
    "Date de l'appel",
    "État du contact",
    "Commentaire",
]

# Vue générale Gironde : Médoc, Bassin d'Arcachon et Bordeaux Métropole
DEFAULT_VIEW = {
    "latitude": 44.91,
    "longitude": -0.93,
    "zoom": 8.35,
}

THEME_COLORS = {
    "Assurance / sinistre": [215, 25, 32, 225],
    "Trésorerie / aides": [241, 145, 0, 225],
    "Activité / fermeture": [111, 66, 193, 225],
    "Salariés / activité partielle": [38, 113, 221, 225],
    "Accès / évacuation": [0, 137, 123, 225],
    "Approvisionnement / clients": [156, 94, 39, 225],
    "Information / orientation": [102, 112, 133, 225],
    "Autre": [78, 89, 105, 225],
}

THEME_HEX = {
    key: "#{:02X}{:02X}{:02X}".format(*value[:3])
    for key, value in THEME_COLORS.items()
}


# ============================================================
# TERRITOIRES / EPCI
# ============================================================

EPCI_COMMUNES: dict[str, list[str]] = {
    "CC Jalle Eau Bourde": [
        "Canéjan",
        "Cestas",
        "Saint-Jean-d'Illac",
    ],
    "Bordeaux Métropole": [
        "Ambarès-et-Lagrave",
        "Ambès",
        "Artigues-près-Bordeaux",
        "Bassens",
        "Bègles",
        "Blanquefort",
        "Bordeaux",
        "Bouliac",
        "Le Bouscat",
        "Bruges",
        "Carbon-Blanc",
        "Cenon",
        "Eysines",
        "Floirac",
        "Gradignan",
        "Le Haillan",
        "Lormont",
        "Martignas-sur-Jalle",
        "Mérignac",
        "Parempuyre",
        "Pessac",
        "Saint-Aubin-de-Médoc",
        "Saint-Louis-de-Montferrand",
        "Saint-Médard-en-Jalles",
        "Saint-Vincent-de-Paul",
        "Talence",
        "Le Taillan-Médoc",
        "Villenave-d'Ornon",
    ],
    "CC Médoc Atlantique": [
        "Carcans",
        "Grayan-et-l'Hôpital",
        "Hourtin",
        "Jau-Dignac-et-Loirac",
        "Lacanau",
        "Le Verdon-sur-Mer",
        "Naujac-sur-Mer",
        "Queyrac",
        "Saint-Vivien-de-Médoc",
        "Soulac-sur-Mer",
        "Talais",
        "Vendays-Montalivet",
        "Vensac",
    ],
    "CC Médoc Cœur de Presqu'île": [
        "Bégadan",
        "Blaignan-Prignac",
        "Cissac-Médoc",
        "Civrac-en-Médoc",
        "Couquèques",
        "Gaillan-en-Médoc",
        "Lesparre-Médoc",
        "Ordonnac",
        "Pauillac",
        "Saint-Christoly-Médoc",
        "Saint-Estèphe",
        "Saint-Germain-d'Esteuil",
        "Saint-Julien-Beychevelle",
        "Saint-Laurent-Médoc",
        "Saint-Sauveur",
        "Saint-Seurin-de-Cadourne",
        "Saint-Yzans-de-Médoc",
        "Vertheuil",
    ],
    "CC Médoc Estuaire": [
        "Arcins",
        "Arsac",
        "Cussac-Fort-Médoc",
        "Labarde",
        "Lamarque",
        "Le Pian-Médoc",
        "Ludon-Médoc",
        "Macau",
        "Margaux-Cantenac",
        "Soussans",
    ],
    "CC Médullienne": [
        "Avensan",
        "Brach",
        "Castelnau-de-Médoc",
        "Le Porge",
        "Le Temple",
        "Listrac-Médoc",
        "Moulis-en-Médoc",
        "Salaunes",
        "Saumos",
        "Sainte-Hélène",
    ],
    "COBAN — Bassin d'Arcachon Nord": [
        "Andernos-les-Bains",
        "Arès",
        "Audenge",
        "Biganos",
        "Lanton",
        "Lège-Cap-Ferret",
        "Marcheprime",
        "Mios",
    ],
    "COBAS — Bassin d'Arcachon Sud": [
        "Arcachon",
        "Gujan-Mestras",
        "La Teste-de-Buch",
        "Le Teich",
    ],
    "CC du Val de l'Eyre": [
        "Belin-Béliet",
        "Le Barp",
        "Lugos",
        "Saint-Magne",
        "Salles",
    ],
}

EPCI_TO_GRAND_TERRITORY = {
    "CC Jalle Eau Bourde": "Ouest bordelais",
    "Bordeaux Métropole": "Bordeaux Métropole",
    "CC Médoc Atlantique": "Médoc",
    "CC Médoc Cœur de Presqu'île": "Médoc",
    "CC Médoc Estuaire": "Médoc",
    "CC Médullienne": "Médoc",
    "COBAN — Bassin d'Arcachon Nord": "Bassin d'Arcachon – Val de l'Eyre",
    "COBAS — Bassin d'Arcachon Sud": "Bassin d'Arcachon – Val de l'Eyre",
    "CC du Val de l'Eyre": "Bassin d'Arcachon – Val de l'Eyre",
}


# ============================================================
# ONGLET LÈGE / CAP-FERRET CONSERVÉ À PART
# ============================================================

LEGE_CENTER_LAT = 44.7935
LEGE_CENTER_LON = -1.1460
LEGE_DEFAULT_ZOOM = 10.4

TRUC_VERT_POINT = {
    "latitude": 44.715108,
    "longitude": -1.249283,
}

POINTE_AUX_CHEVAUX_POINT = {
    "latitude": 44.718090,
    "longitude": -1.204960,
}

SECTOR_BOUNDS = {
    "west": -1.285,
    "east": -1.105,
    "south": 44.585,
    "north": 45.000,
}

LEGE_SECTOR_POLYGON = [
    [SECTOR_BOUNDS["west"], SECTOR_BOUNDS["north"]],
    [SECTOR_BOUNDS["east"], SECTOR_BOUNDS["north"]],
    [POINTE_AUX_CHEVAUX_POINT["longitude"], POINTE_AUX_CHEVAUX_POINT["latitude"]],
    [TRUC_VERT_POINT["longitude"], TRUC_VERT_POINT["latitude"]],
]

CAP_FERRET_SECTOR_POLYGON = [
    [TRUC_VERT_POINT["longitude"], TRUC_VERT_POINT["latitude"]],
    [POINTE_AUX_CHEVAUX_POINT["longitude"], POINTE_AUX_CHEVAUX_POINT["latitude"]],
    [SECTOR_BOUNDS["east"], SECTOR_BOUNDS["south"]],
    [SECTOR_BOUNDS["west"], SECTOR_BOUNDS["south"]],
]


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
            max-width: 1540px;
            padding-top: 1.1rem;
            padding-bottom: 3rem;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #111827 0%, #172235 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }}

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
        }}

        [data-testid="stSidebar"] .stRadio label:hover {{
            background: rgba(255,255,255,.08);
        }}

        [data-testid="stMainBlockContainer"] input,
        [data-testid="stMainBlockContainer"] textarea {{
            background: #FFFFFF !important;
            color: #172033 !important;
        }}

        [data-testid="stMainBlockContainer"] div[data-baseweb="select"] > div {{
            background: #FFFFFF !important;
            color: #172033 !important;
        }}

        .sidebar-brand {{
            padding: .65rem .2rem 1rem;
        }}

        .sidebar-brand-title {{
            color: #FFFFFF;
            font-size: 1.08rem;
            font-weight: 850;
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
            margin-top: .85rem;
            border-radius: 999px;
            background: var(--cma-red);
        }}

        .app-header {{
            position: relative;
            overflow: hidden;
            padding: 1.45rem 1.65rem;
            margin-bottom: 1.15rem;
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
            margin-bottom: .55rem;
            color: #FFB6C1;
            font-size: .75rem;
            font-weight: 850;
            letter-spacing: .1em;
            text-transform: uppercase;
        }}

        .app-header-title {{
            position: relative;
            z-index: 2;
            margin: 0;
            color: #FFFFFF !important;
            font-size: 2rem;
            font-weight: 850;
            letter-spacing: -.035em;
        }}

        .app-header-subtitle {{
            position: relative;
            z-index: 2;
            max-width: 900px;
            margin-top: .48rem;
            color: rgba(255,255,255,.84);
            font-size: .94rem;
        }}

        .section-title {{
            margin-top: .35rem;
            margin-bottom: .15rem;
            color: var(--text);
            font-size: 1.18rem;
            font-weight: 850;
        }}

        .section-subtitle {{
            margin-bottom: .9rem;
            color: var(--muted);
            font-size: .85rem;
        }}

        .metric-card {{
            min-height: 125px;
            padding: 1rem 1.05rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: #FFFFFF;
            box-shadow: 0 7px 22px rgba(16,24,40,.055);
        }}

        .metric-label {{
            color: var(--muted);
            font-size: .76rem;
            font-weight: 700;
        }}

        .metric-value {{
            margin-top: .2rem;
            color: var(--text);
            font-size: 2rem;
            font-weight: 850;
            line-height: 1;
        }}

        .metric-detail {{
            margin-top: .5rem;
            color: var(--muted);
            font-size: .72rem;
        }}

        .soft-panel {{
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: #FFFFFF;
            box-shadow: 0 7px 22px rgba(16,24,40,.05);
        }}

        [data-testid="stDataFrame"] {{
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 14px;
        }}

        .footer-note {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: .72rem;
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# ÉTAT
# ============================================================

def initialize_state() -> None:
    if "crisis_data" not in st.session_state:
        st.session_state.crisis_data = pd.DataFrame()
    if "lege_data" not in st.session_state:
        st.session_state.lege_data = pd.DataFrame()
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Tableau de bord"
    if "nav_radio" not in st.session_state:
        st.session_state.nav_radio = st.session_state.current_page


# ============================================================
# OUTILS GÉNÉRAUX
# ============================================================

def render_header(title: str, subtitle: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-header-kicker">● {html.escape(kicker)}</div>
            <h1 class="app-header-title">{html.escape(title)}</h1>
            <div class="app-header-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="section-title">{html.escape(title)}</div>'
        f'<div class="section-subtitle">{html.escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def render_metric(label: str, value: Any, detail: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-detail">{html.escape(str(detail))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        '<div class="footer-note">'
        'CMA — Cartographie cellule de crise · Données conservées uniquement dans la session active'
        '</div>',
        unsafe_allow_html=True,
    )


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_place(value: Any) -> str:
    text = normalize_text(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[-’']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_call_date(value: Any) -> pd.Timestamp | pd.NaT:
    if pd.isna(value) or normalize_text(value) == "":
        return pd.NaT
    return pd.to_datetime(value, errors="coerce", dayfirst=True)


def commune_to_epci(commune: str) -> tuple[str, str]:
    normalized = normalize_place(commune)
    for epci, communes in EPCI_COMMUNES.items():
        for candidate in communes:
            if normalize_place(candidate) == normalized:
                return epci, EPCI_TO_GRAND_TERRITORY[epci]
    return "Autre / à vérifier", "Autre territoire"


def normalize_contact_state(value: Any) -> str:
    """Uniformise les libellés provenant d'Excel ou de Microsoft Lists."""
    text = normalize_place(value)

    aliases = {
        "entreprise contactee": "Entreprise contactée",
        "contacte": "Entreprise contactée",
        "contactee": "Entreprise contactée",
        "message vocal mail envoye": "Message vocal & mail envoyé",
        "message vocal et mail envoye": "Message vocal & mail envoyé",
        "message vocal & mail envoye": "Message vocal & mail envoyé",
        "message vocal": "Message vocal & mail envoyé",
        "mail envoye": "Message vocal & mail envoyé",
        "mauvais numero": "Mauvais numéro",
        "numero incorrect": "Mauvais numéro",
        "deja contactee": "Déjà contactée",
        "deja contacte": "Déjà contactée",
        "a rappeler": "À rappeler",
        "rappel": "À rappeler",
        "non renseigne": "Non renseigné",
        "": "Non renseigné",
    }
    return aliases.get(text, normalize_text(value) or "Non renseigné")


def contact_progress_rate(df: pd.DataFrame) -> float:
    """Part des lignes dont le traitement est considéré comme terminé."""
    if df.empty or "État du contact" not in df.columns:
        return 0.0
    completed = df["État du contact"].isin(FINAL_CONTACT_STATES).sum()
    return round(float(completed) / len(df) * 100, 1)


def contact_state_counts(df: pd.DataFrame) -> dict[str, int]:
    if df.empty or "État du contact" not in df.columns:
        return {state: 0 for state in CONTACT_STATES}
    counts = df["État du contact"].value_counts().to_dict()
    return {state: int(counts.get(state, 0)) for state in CONTACT_STATES}


def classify_comment_theme(comment: str) -> str:
    text = normalize_place(comment)

    keyword_groups = [
        (
            "Assurance / sinistre",
            ["assurance", "sinistre", "expert", "degat", "dommage", "indemnisation"],
        ),
        (
            "Salariés / activité partielle",
            [
                "chomage partiel",
                "activite partielle",
                "salarie",
                "salariés",
                "emploi",
            ],
        ),
        (
            "Trésorerie / aides",
            [
                "tresorerie",
                "aide",
                "cpsti",
                "urssaf",
                "impot",
                "banque",
                "echeance",
                "fonds",
            ],
        ),
        (
            "Accès / évacuation",
            [
                "evacuation",
                "evacue",
                "acces",
                "inaccessible",
                "route fermee",
                "fermeture de route",
                "reintegration",
            ],
        ),
        (
            "Activité / fermeture",
            [
                "fermeture",
                "activite arretee",
                "arret activite",
                "perte exploitation",
                "perte d exploitation",
                "baisse activite",
                "reprise",
            ],
        ),
        (
            "Approvisionnement / clients",
            [
                "fournisseur",
                "approvisionnement",
                "livraison",
                "client",
                "annulation",
                "commande",
            ],
        ),
        (
            "Information / orientation",
            ["information", "renseignement", "orientation", "transmis", "contact"],
        ),
    ]

    for theme, keywords in keyword_groups:
        if any(keyword in text for keyword in keywords):
            return theme

    return "Autre"


def safe_tooltip_text(value: Any, max_length: int = 500) -> str:
    text = normalize_text(value)
    text = text.replace("<", "‹").replace(">", "›")
    if len(text) > max_length:
        return text[: max_length - 1] + "…"
    return text


# ============================================================
# IMPORT / GÉOCODAGE
# ============================================================

def create_crisis_excel_template() -> bytes:
    template = pd.DataFrame(
        [
            {
                "Nom de l'entreprise": "Entreprise exemple",
                "Adresse": "1 avenue de la Mairie",
                "Commune": "Lège-Cap-Ferret",
                "Date de l'appel": date.today().strftime("%d/%m/%Y"),
                "État du contact": "Entreprise contactée",
                "Commentaire": "Entreprise contactée et orientée vers son assurance.",
            }
        ]
    )
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        template.to_excel(writer, index=False, sheet_name="Entreprises appelées")
    return buffer.getvalue()


def normalize_import_column(column: Any) -> str:
    text = normalize_place(column)
    aliases = {
        "nom": "Nom de l'entreprise",
        "nom entreprise": "Nom de l'entreprise",
        "nom de l entreprise": "Nom de l'entreprise",
        "entreprise": "Nom de l'entreprise",
        "raison sociale": "Nom de l'entreprise",
        "adresse": "Adresse",
        "adresse complete": "Adresse",
        "adresse postale": "Adresse",
        "commune": "Commune",
        "ville": "Commune",
        "date": "Date de l'appel",
        "date appel": "Date de l'appel",
        "date de l appel": "Date de l'appel",
        "etat": "État du contact",
        "etat contact": "État du contact",
        "etat du contact": "État du contact",
        "statut contact": "État du contact",
        "statut du contact": "État du contact",
        "commentaire": "Commentaire",
        "commentaires": "Commentaire",
        "observation": "Commentaire",
        "observations": "Commentaire",
    }
    return aliases.get(text, str(column).strip())


def read_uploaded_file(uploaded_file) -> tuple[pd.DataFrame | None, list[str]]:
    warnings: list[str] = []

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, sep=None, engine="python", dtype=str)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(
                    uploaded_file,
                    sep=None,
                    engine="python",
                    dtype=str,
                    encoding="latin-1",
                )
        else:
            df = pd.read_excel(uploaded_file, dtype=str)
    except Exception as exc:
        return None, [f"Impossible de lire le fichier : {exc}"]

    df = df.rename(columns={column: normalize_import_column(column) for column in df.columns})

    missing = [column for column in IMPORT_COLUMNS if column not in df.columns]
    if missing:
        return None, [
            "Colonnes manquantes : " + ", ".join(missing),
            "Les colonnes attendues sont : " + " | ".join(IMPORT_COLUMNS),
        ]

    clean = df[IMPORT_COLUMNS].copy()

    for column in [
        "Nom de l'entreprise",
        "Adresse",
        "Commune",
        "État du contact",
        "Commentaire",
    ]:
        clean[column] = clean[column].fillna("").astype(str).str.strip()

    clean["État du contact"] = clean["État du contact"].apply(normalize_contact_state)
    clean["Date de l'appel"] = clean["Date de l'appel"].apply(parse_call_date)

    invalid = (
        clean["Nom de l'entreprise"].eq("")
        | clean["Adresse"].eq("")
        | clean["Commune"].eq("")
    )
    if invalid.any():
        warnings.append(
            f"{int(invalid.sum())} ligne(s) sans nom, adresse ou commune seront ignorées."
        )
        clean = clean.loc[~invalid].copy()

    invalid_dates = clean["Date de l'appel"].isna()
    if invalid_dates.any():
        warnings.append(
            f"{int(invalid_dates.sum())} date(s) non reconnue(s). Les lignes restent importées."
        )

    clean = clean.drop_duplicates(
        subset=["Nom de l'entreprise", "Adresse", "Commune", "Date de l'appel"],
        keep="first",
    ).reset_index(drop=True)

    if clean.empty:
        return None, warnings + ["Aucune ligne exploitable n'a été trouvée."]

    return clean, warnings


def build_address_query(address: str, commune: str) -> str:
    combined = f"{address}, {commune}, Gironde"
    return re.sub(r"\s+", " ", combined).strip()


@st.cache_data(show_spinner=False, ttl=86400)
def geocode_address(address: str, commune: str) -> dict[str, Any]:
    query = build_address_query(address, commune)

    try:
        response = requests.get(
            GEOCODING_URL,
            params={
                "q": query,
                "limit": 5,
                "autocomplete": 0,
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return {
            "Statut géocodage": "Erreur API",
            "Erreur géocodage": str(exc),
        }
    except ValueError:
        return {
            "Statut géocodage": "Réponse invalide",
            "Erreur géocodage": "Réponse JSON invalide.",
        }

    features = payload.get("features", [])
    if not features:
        return {
            "Statut géocodage": "Non localisée",
            "Erreur géocodage": "Aucun résultat.",
        }

    normalized_commune = normalize_place(commune)
    selected = None

    for feature in features:
        properties = feature.get("properties", {})
        candidate_city = (
            properties.get("city")
            or properties.get("municipality")
            or properties.get("city_name")
            or ""
        )
        candidate_label = properties.get("label") or ""
        if (
            normalize_place(candidate_city) == normalized_commune
            or normalized_commune in normalize_place(candidate_label)
        ):
            selected = feature
            break

    if selected is None:
        selected = features[0]

    properties = selected.get("properties", {})
    geometry = selected.get("geometry", {})
    coordinates = geometry.get("coordinates", [])

    if len(coordinates) < 2:
        return {
            "Statut géocodage": "Coordonnées absentes",
            "Erreur géocodage": "Résultat sans coordonnées.",
        }

    longitude, latitude = float(coordinates[0]), float(coordinates[1])
    recognized_city = (
        properties.get("city")
        or properties.get("municipality")
        or properties.get("city_name")
        or ""
    )
    recognized_label = properties.get("label") or query
    postcode = properties.get("postcode") or ""
    score = properties.get("score")

    try:
        score_value = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_value = None

    city_match = normalize_place(recognized_city) == normalized_commune

    if not city_match:
        status = "À vérifier — commune différente"
    elif score_value is not None and score_value < 0.50:
        status = "À vérifier — score faible"
    else:
        status = "Localisée"

    return {
        "Adresse reconnue": recognized_label,
        "Commune reconnue": recognized_city,
        "Code postal reconnu": postcode,
        "Latitude": latitude,
        "Longitude": longitude,
        "Score géocodage": score_value,
        "Statut géocodage": status,
        "Erreur géocodage": "",
    }


def enrich_dataframe(source_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total = len(source_df)
    progress = st.progress(0)
    status_box = st.empty()

    for position, (_, row) in enumerate(source_df.iterrows(), start=1):
        company_name = row["Nom de l'entreprise"]
        status_box.caption(
            f"Géocodage {position}/{total} — {company_name}"
        )
        geocoded = geocode_address(row["Adresse"], row["Commune"])
        epci, grand_territory = commune_to_epci(row["Commune"])
        comment = row["Commentaire"]

        rows.append(
            {
                "Nom de l'entreprise": row["Nom de l'entreprise"],
                "Adresse": row["Adresse"],
                "Commune": row["Commune"],
                "Date de l'appel": row["Date de l'appel"],
                "État du contact": normalize_contact_state(row["État du contact"]),
                "Commentaire": comment,
                "Thématique": classify_comment_theme(comment),
                "EPCI / CDC": epci,
                "Grand territoire": grand_territory,
                **geocoded,
            }
        )

        progress.progress(position / total)

    status_box.empty()
    progress.empty()

    result = pd.DataFrame(rows)
    if not result.empty:
        result["Date de l'appel"] = pd.to_datetime(
            result["Date de l'appel"],
            errors="coerce",
        )
    return result


# ============================================================
# FILTRES
# ============================================================

def render_filters(df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    """
    Panneau de filtres compact :
    - un onglet Territoire ;
    - un onglet Suivi des appels ;
    - un onglet Recherche et qualité.
    Les sélecteurs utilisent une valeur unique avec l'option « Tous »,
    ce qui évite l'accumulation de pastilles à l'écran.
    """
    if df.empty:
        return df

    with st.container(border=True):
        header_col, count_col = st.columns([4, 1])
        with header_col:
            st.markdown("### Filtres du rapport")
            st.caption(
                "Choisissez un périmètre territorial, une période et un état de contact. "
                "La carte, les indicateurs et le PDF utilisent exactement ces critères."
            )
        with count_col:
            st.metric("Base active", len(df))

        territory_tab, followup_tab, search_tab = st.tabs(
            ["📍 Territoire", "☎️ Suivi des appels", "🔎 Recherche et qualité"]
        )

        date_series = pd.to_datetime(df["Date de l'appel"], errors="coerce")
        valid_dates = date_series.dropna()

        with territory_tab:
            cols = st.columns([1.2, 1.2, 1.2, 1.35], gap="large")

            grand_options = sorted(df["Grand territoire"].dropna().unique())
            with cols[0]:
                selected_grand = st.selectbox(
                    "Grand territoire",
                    ["Tous"] + grand_options,
                    key=f"{key_prefix}_grand",
                )

            grand_source = (
                df[df["Grand territoire"] == selected_grand]
                if selected_grand != "Tous"
                else df
            )

            epci_options = sorted(grand_source["EPCI / CDC"].dropna().unique())
            with cols[1]:
                selected_epci = st.selectbox(
                    "CDC / EPCI",
                    ["Tous"] + epci_options,
                    key=f"{key_prefix}_epci",
                )

            epci_source = (
                grand_source[grand_source["EPCI / CDC"] == selected_epci]
                if selected_epci != "Tous"
                else grand_source
            )

            commune_options = sorted(epci_source["Commune"].dropna().unique())
            with cols[2]:
                selected_commune = st.selectbox(
                    "Commune",
                    ["Toutes"] + commune_options,
                    key=f"{key_prefix}_commune",
                )

            with cols[3]:
                if valid_dates.empty:
                    selected_period = None
                    st.date_input(
                        "Période d'appel",
                        value=(date.today(), date.today()),
                        disabled=True,
                        key=f"{key_prefix}_period_disabled",
                    )
                else:
                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()
                    selected_period = st.date_input(
                        "Période d'appel",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key=f"{key_prefix}_period",
                    )

        with followup_tab:
            cols = st.columns(3, gap="large")

            available_states = [
                state
                for state in CONTACT_STATES
                if state in set(df["État du contact"].dropna().unique())
            ]
            with cols[0]:
                selected_contact_state = st.selectbox(
                    "État du contact",
                    ["Tous"] + available_states,
                    key=f"{key_prefix}_contact_state",
                )

            theme_options = sorted(df["Thématique"].dropna().unique())
            with cols[1]:
                selected_theme = st.selectbox(
                    "Thématique du commentaire",
                    ["Toutes"] + theme_options,
                    key=f"{key_prefix}_theme",
                )

            with cols[2]:
                comments_only = st.toggle(
                    "Uniquement les lignes avec commentaire",
                    value=False,
                    key=f"{key_prefix}_comments",
                )

        with search_tab:
            cols = st.columns([1.5, 1.2], gap="large")

            with cols[0]:
                search = st.text_input(
                    "Rechercher une entreprise",
                    placeholder="Saisir une partie du nom…",
                    key=f"{key_prefix}_search",
                )

            geo_options = sorted(
                df["Statut géocodage"].fillna("Non renseigné").unique()
            )
            with cols[1]:
                selected_geo = st.selectbox(
                    "Qualité de géolocalisation",
                    ["Toutes"] + geo_options,
                    key=f"{key_prefix}_geo",
                )

    filtered = df.copy()

    if selected_grand != "Tous":
        filtered = filtered[filtered["Grand territoire"] == selected_grand]
    if selected_epci != "Tous":
        filtered = filtered[filtered["EPCI / CDC"] == selected_epci]
    if selected_commune != "Toutes":
        filtered = filtered[filtered["Commune"] == selected_commune]
    if selected_contact_state != "Tous":
        filtered = filtered[
            filtered["État du contact"] == selected_contact_state
        ]
    if selected_theme != "Toutes":
        filtered = filtered[filtered["Thématique"] == selected_theme]
    if selected_geo != "Toutes":
        filtered = filtered[filtered["Statut géocodage"] == selected_geo]
    if comments_only:
        filtered = filtered[
            filtered["Commentaire"].astype(str).str.strip().ne("")
        ]
    if search:
        q = normalize_place(search)
        filtered = filtered[
            filtered["Nom de l'entreprise"]
            .astype(str)
            .apply(normalize_place)
            .str.contains(q, na=False)
        ]

    if selected_period and isinstance(selected_period, tuple) and len(selected_period) == 2:
        start_date, end_date = selected_period
        filtered_dates = pd.to_datetime(
            filtered["Date de l'appel"],
            errors="coerce",
        )
        mask = (
            filtered_dates.dt.date.ge(start_date)
            & filtered_dates.dt.date.le(end_date)
        )
        filtered = filtered[mask.fillna(False)]

    st.caption(
        f"**{len(filtered)} entreprise(s)** correspondent aux filtres sélectionnés."
    )
    return filtered


# ============================================================
# CARTE PRINCIPALE
# ============================================================

def render_crisis_map(
    df: pd.DataFrame,
    height: int = 680,
    heatmap: bool = False,
) -> None:
    valid = df.dropna(subset=["Latitude", "Longitude"]).copy()

    if valid.empty:
        st.info("Aucun point géolocalisé ne correspond aux filtres.")
        return

    valid["Couleur"] = valid["État du contact"].map(CONTACT_STATE_COLORS)
    valid["Couleur"] = valid["Couleur"].apply(
        lambda value: value if isinstance(value, list) else CONTACT_STATE_COLORS["Non renseigné"]
    )
    valid["Rayon"] = 110
    valid["Nom_affichage"] = valid["Nom de l'entreprise"].apply(safe_tooltip_text)
    valid["Adresse_affichage"] = valid["Adresse"].apply(safe_tooltip_text)
    valid["Commentaire_affichage"] = valid["Commentaire"].apply(safe_tooltip_text)
    valid["Date_affichage"] = pd.to_datetime(
        valid["Date de l'appel"],
        errors="coerce",
    ).dt.strftime("%d/%m/%Y").fillna("Non renseignée")

    layers: list[pdk.Layer] = []

    if heatmap:
        layers.append(
            pdk.Layer(
                "HeatmapLayer",
                data=valid,
                get_position="[Longitude, Latitude]",
                get_weight=1,
                radius_pixels=45,
                intensity=1.2,
                threshold=0.04,
                opacity=0.65,
                pickable=False,
            )
        )

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=valid,
            get_position="[Longitude, Latitude]",
            get_fill_color="Couleur",
            get_line_color=[255, 255, 255, 245],
            get_radius="Rayon",
            radius_min_pixels=7,
            radius_max_pixels=18,
            line_width_min_pixels=2,
            pickable=True,
            stroked=True,
            filled=True,
            opacity=0.92,
        )
    )

    center_lat = float(valid["Latitude"].mean())
    center_lon = float(valid["Longitude"].mean())

    deck = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=DEFAULT_VIEW["zoom"],
            pitch=0,
        ),
        layers=layers,
        tooltip={
            "html": """
                <div style="min-width:310px;max-width:420px;font-family:Arial,sans-serif">
                    <div style="font-size:16px;font-weight:800;margin-bottom:8px">
                        {Nom_affichage}
                    </div>
                    <div><b>Adresse :</b> {Adresse_affichage}</div>
                    <div><b>Commune :</b> {Commune}</div>
                    <div><b>CDC / EPCI :</b> {EPCI / CDC}</div>
                    <div><b>Date de l'appel :</b> {Date_affichage}</div>
                    <div><b>État du contact :</b> {État du contact}</div>
                    <div><b>Thématique :</b> {Thématique}</div>
                    <div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.25)">
                        <b>Commentaire :</b><br>{Commentaire_affichage}
                    </div>
                </div>
            """,
            "style": {
                "backgroundColor": "#111827",
                "color": "white",
                "borderRadius": "12px",
                "padding": "13px",
            },
        },
    )

    st.pydeck_chart(deck, height=height, use_container_width=True)


def render_contact_state_legend(states: list[str]) -> None:
    html_parts = []
    for state in states:
        color = CONTACT_STATE_HEX.get(state, "#667085")
        html_parts.append(
            f'<span style="display:inline-flex;align-items:center;margin-right:14px;'
            f'margin-bottom:7px;font-size:12px;color:#667085">'
            f'<span style="width:9px;height:9px;border-radius:50%;background:{color};'
            f'margin-right:5px"></span>{html.escape(state)}</span>'
        )
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_theme_legend(themes: list[str]) -> None:
    html_parts = []
    for theme in themes:
        color = THEME_HEX.get(theme, "#667085")
        html_parts.append(
            f'<span style="display:inline-flex;align-items:center;margin-right:14px;'
            f'margin-bottom:7px;font-size:12px;color:#667085">'
            f'<span style="width:9px;height:9px;border-radius:50%;background:{color};'
            f'margin-right:5px"></span>{html.escape(theme)}</span>'
        )
    st.markdown("".join(html_parts), unsafe_allow_html=True)


# ============================================================
# EXPORTS / RAPPORT
# ============================================================

def create_results_excel(df: pd.DataFrame) -> bytes:
    export_df = df.copy()
    if "Date de l'appel" in export_df.columns:
        export_df["Date de l'appel"] = pd.to_datetime(
            export_df["Date de l'appel"],
            errors="coerce",
        ).dt.strftime("%d/%m/%Y")

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Entreprises appelées")
        worksheet = writer.sheets["Entreprises appelées"]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        widths = {
            "A": 34,
            "B": 45,
            "C": 24,
            "D": 17,
            "E": 58,
            "F": 30,
            "G": 35,
            "H": 28,
            "I": 50,
            "J": 24,
            "K": 19,
            "L": 14,
            "M": 14,
            "N": 16,
            "O": 30,
            "P": 40,
        }
        for column, width in widths.items():
            worksheet.column_dimensions[column].width = width

    return buffer.getvalue()


def report_metrics(df: pd.DataFrame) -> dict[str, Any]:
    localized = int(df["Latitude"].notna().sum()) if "Latitude" in df else 0
    comments = int(df["Commentaire"].astype(str).str.strip().ne("").sum()) if not df.empty else 0
    dates = pd.to_datetime(df["Date de l'appel"], errors="coerce") if not df.empty else pd.Series(dtype="datetime64[ns]")

    return {
        "total": len(df),
        "communes": int(df["Commune"].nunique()) if not df.empty else 0,
        "epci": int(df["EPCI / CDC"].nunique()) if not df.empty else 0,
        "localized": localized,
        "comments": comments,
        "first_date": dates.min().strftime("%d/%m/%Y") if not dates.dropna().empty else "Non renseignée",
        "last_date": dates.max().strftime("%d/%m/%Y") if not dates.dropna().empty else "Non renseignée",
    }


def prepare_pdf_map_points(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Nettoie les coordonnées avant la carte PDF :
    - conserve uniquement les points géocodés ;
    - écarte les coordonnées hors emprise Gironde élargie ;
    - écarte les valeurs aberrantes qui écraseraient le zoom.
    """
    valid = df.dropna(subset=["Latitude", "Longitude"]).copy()
    if valid.empty:
        return valid, 0

    initial_count = len(valid)

    valid = valid[
        valid["Longitude"].between(-1.35, 0.25)
        & valid["Latitude"].between(44.15, 45.75)
    ].copy()

    if len(valid) >= 8:
        lon_q1 = valid["Longitude"].quantile(0.25)
        lon_q3 = valid["Longitude"].quantile(0.75)
        lat_q1 = valid["Latitude"].quantile(0.25)
        lat_q3 = valid["Latitude"].quantile(0.75)

        lon_iqr = max(lon_q3 - lon_q1, 0.025)
        lat_iqr = max(lat_q3 - lat_q1, 0.025)

        robust_mask = (
            valid["Longitude"].between(
                lon_q1 - 4.0 * lon_iqr,
                lon_q3 + 4.0 * lon_iqr,
            )
            & valid["Latitude"].between(
                lat_q1 - 4.0 * lat_iqr,
                lat_q3 + 4.0 * lat_iqr,
            )
        )

        # Ne pas supprimer un petit groupe territorial réellement filtré.
        robust = valid[robust_mask].copy()
        if len(robust) >= max(3, int(len(valid) * 0.85)):
            valid = robust

    excluded_count = initial_count - len(valid)
    return valid, excluded_count


def create_osm_report_map(df: pd.DataFrame) -> tuple[bytes | None, int]:
    """
    Génère une véritable carte OpenStreetMap pour le PDF.

    En cas d'indisponibilité temporaire des tuiles, la fonction renvoie None
    et le rapport utilise automatiquement une représentation de secours.
    """
    valid, excluded_count = prepare_pdf_map_points(df)

    if valid.empty:
        return None, excluded_count

    try:
        static_map = StaticMap(
            1500,
            900,
            url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        )

        for _, row in valid.iterrows():
            state = str(row.get("État du contact", "Non renseigné"))
            marker_color = CONTACT_STATE_HEX.get(state, "#667085")
            static_map.add_marker(
                CircleMarker(
                    (
                        float(row["Longitude"]),
                        float(row["Latitude"]),
                    ),
                    marker_color,
                    10,
                )
            )

        image = static_map.render()
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        return buffer.getvalue(), excluded_count

    except Exception:
        return None, excluded_count


def create_fallback_report_map(df: pd.DataFrame) -> Drawing:
    """Carte de secours compacte si les tuiles OSM ne sont pas disponibles."""
    valid, excluded_count = prepare_pdf_map_points(df)
    width = 25.2 * cm
    height = 14.6 * cm
    drawing = Drawing(width, height)

    drawing.add(
        Rect(
            0,
            0,
            width,
            height,
            fillColor=colors.HexColor("#F2F4F7"),
            strokeColor=colors.HexColor("#D0D5DD"),
            strokeWidth=0.8,
        )
    )

    if valid.empty:
        drawing.add(
            String(
                width / 2,
                height / 2,
                "Aucune entreprise géolocalisée pour les filtres sélectionnés",
                fontName="Helvetica",
                fontSize=11,
                textAnchor="middle",
                fillColor=colors.HexColor("#667085"),
            )
        )
        return drawing

    plot_left = 25
    plot_bottom = 25
    plot_right = width - 20
    plot_top = height - 20

    lon_min = float(valid["Longitude"].min())
    lon_max = float(valid["Longitude"].max())
    lat_min = float(valid["Latitude"].min())
    lat_max = float(valid["Latitude"].max())

    if abs(lon_max - lon_min) < 0.002:
        lon_min -= 0.01
        lon_max += 0.01
    if abs(lat_max - lat_min) < 0.002:
        lat_min -= 0.01
        lat_max += 0.01

    lon_margin = max((lon_max - lon_min) * 0.12, 0.008)
    lat_margin = max((lat_max - lat_min) * 0.12, 0.008)
    lon_min -= lon_margin
    lon_max += lon_margin
    lat_min -= lat_margin
    lat_max += lat_margin

    def project(longitude: float, latitude: float) -> tuple[float, float]:
        x = plot_left + (
            (longitude - lon_min) / (lon_max - lon_min)
        ) * (plot_right - plot_left)
        y = plot_bottom + (
            (latitude - lat_min) / (lat_max - lat_min)
        ) * (plot_top - plot_bottom)
        return x, y

    for _, row in valid.iterrows():
        x, y = project(float(row["Longitude"]), float(row["Latitude"]))
        state = str(row.get("État du contact", "Non renseigné"))
        drawing.add(
            Circle(
                x,
                y,
                4.1,
                fillColor=colors.HexColor(
                    CONTACT_STATE_HEX.get(state, "#667085")
                ),
                strokeColor=colors.white,
                strokeWidth=0.7,
            )
        )

    return drawing


def create_horizontal_bar_chart(
    data: pd.Series,
    title: str,
    width: float = 12.1 * cm,
    height: float = 7.1 * cm,
    max_items: int = 8,
) -> Drawing:
    """Graphique en barres horizontal natif ReportLab."""
    drawing = Drawing(width, height)

    drawing.add(
        Rect(
            0,
            0,
            width,
            height,
            fillColor=colors.white,
            strokeColor=colors.HexColor("#E4E7EC"),
            strokeWidth=0.7,
        )
    )
    drawing.add(
        Rect(
            0,
            height - 0.65 * cm,
            width,
            0.65 * cm,
            fillColor=colors.HexColor("#172033"),
            strokeColor=colors.HexColor("#172033"),
        )
    )
    drawing.add(
        String(
            10,
            height - 0.43 * cm,
            title,
            fontName="Helvetica-Bold",
            fontSize=9,
            fillColor=colors.white,
        )
    )

    clean = data.dropna().sort_values(ascending=False).head(max_items)
    if clean.empty:
        drawing.add(
            String(
                width / 2,
                height / 2,
                "Aucune donnée",
                fontName="Helvetica",
                fontSize=9,
                textAnchor="middle",
                fillColor=colors.HexColor("#667085"),
            )
        )
        return drawing

    max_value = max(float(clean.max()), 1.0)
    chart_top = height - 1.0 * cm
    chart_bottom = 0.35 * cm
    available_height = chart_top - chart_bottom
    row_height = available_height / len(clean)
    label_width = 4.8 * cm
    bar_left = label_width
    bar_right = width - 1.1 * cm
    bar_max_width = bar_right - bar_left

    for index, (label, value) in enumerate(clean.items()):
        y = chart_top - (index + 0.72) * row_height
        label_text = str(label)
        if len(label_text) > 28:
            label_text = label_text[:27] + "…"

        drawing.add(
            String(
                8,
                y,
                label_text,
                fontName="Helvetica",
                fontSize=6.7,
                fillColor=colors.HexColor("#344054"),
            )
        )

        drawing.add(
            Rect(
                bar_left,
                y - 1.5,
                bar_max_width,
                5.8,
                fillColor=colors.HexColor("#F2F4F7"),
                strokeColor=None,
            )
        )

        value_width = bar_max_width * float(value) / max_value
        drawing.add(
            Rect(
                bar_left,
                y - 1.5,
                value_width,
                5.8,
                fillColor=colors.HexColor(CMA_RED),
                strokeColor=None,
            )
        )

        drawing.add(
            String(
                min(bar_left + value_width + 4, width - 22),
                y,
                str(int(value)),
                fontName="Helvetica-Bold",
                fontSize=6.7,
                fillColor=colors.HexColor("#172033"),
            )
        )

    return drawing


def create_daily_calls_chart(
    df: pd.DataFrame,
    width: float = 25.0 * cm,
    height: float = 6.6 * cm,
) -> Drawing:
    """Mini graphique chronologique en colonnes pour le rapport."""
    drawing = Drawing(width, height)

    drawing.add(
        Rect(
            0,
            0,
            width,
            height,
            fillColor=colors.white,
            strokeColor=colors.HexColor("#E4E7EC"),
            strokeWidth=0.7,
        )
    )
    drawing.add(
        Rect(
            0,
            height - 0.65 * cm,
            width,
            0.65 * cm,
            fillColor=colors.HexColor("#172033"),
            strokeColor=colors.HexColor("#172033"),
        )
    )
    drawing.add(
        String(
            10,
            height - 0.43 * cm,
            "Évolution quotidienne des appels",
            fontName="Helvetica-Bold",
            fontSize=9,
            fillColor=colors.white,
        )
    )

    dates = pd.to_datetime(df["Date de l'appel"], errors="coerce").dropna()
    if dates.empty:
        drawing.add(
            String(
                width / 2,
                height / 2,
                "Aucune date exploitable",
                textAnchor="middle",
                fontName="Helvetica",
                fontSize=9,
                fillColor=colors.HexColor("#667085"),
            )
        )
        return drawing

    daily = dates.dt.date.value_counts().sort_index()
    max_days = 30
    if len(daily) > max_days:
        daily = daily.tail(max_days)

    chart_left = 1.0 * cm
    chart_right = width - 0.5 * cm
    chart_bottom = 0.75 * cm
    chart_top = height - 1.0 * cm
    chart_width = chart_right - chart_left
    chart_height = chart_top - chart_bottom
    max_value = max(float(daily.max()), 1.0)
    slot_width = chart_width / len(daily)
    bar_width = max(slot_width * 0.62, 2.0)

    for index, (day, value) in enumerate(daily.items()):
        x = chart_left + index * slot_width + (slot_width - bar_width) / 2
        bar_height = chart_height * float(value) / max_value

        drawing.add(
            Rect(
                x,
                chart_bottom,
                bar_width,
                bar_height,
                fillColor=colors.HexColor(CMA_RED),
                strokeColor=None,
            )
        )

        if index % max(1, len(daily) // 8) == 0 or index == len(daily) - 1:
            drawing.add(
                String(
                    x,
                    chart_bottom - 10,
                    pd.Timestamp(day).strftime("%d/%m"),
                    fontName="Helvetica",
                    fontSize=5.8,
                    fillColor=colors.HexColor("#667085"),
                )
            )

    return drawing


def report_scope_text(df: pd.DataFrame) -> str:
    if df.empty:
        return "Aucune donnée dans le périmètre sélectionné."

    dates = pd.to_datetime(df["Date de l'appel"], errors="coerce").dropna()
    period = (
        f"du {dates.min().strftime('%d/%m/%Y')} au {dates.max().strftime('%d/%m/%Y')}"
        if not dates.empty
        else "période non renseignée"
    )

    epcis = sorted(df["EPCI / CDC"].dropna().unique())
    communes = sorted(df["Commune"].dropna().unique())

    epci_text = epcis[0] if len(epcis) == 1 else f"{len(epcis)} CDC / EPCI"
    commune_text = (
        communes[0] if len(communes) == 1 else f"{len(communes)} communes"
    )

    return f"Périmètre : {epci_text} - {commune_text} - période {period}."


def create_pdf_report(df: pd.DataFrame) -> bytes:
    """Génère un rapport PDF directement téléchargeable depuis Streamlit."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.25 * cm,
        leftMargin=1.25 * cm,
        topMargin=1.15 * cm,
        bottomMargin=1.15 * cm,
        title="Rapport cellule de crise CMA",
        author="CMA Nouvelle-Aquitaine",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#172033"),
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitleCMA",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor(CMA_RED),
            spaceBefore=10,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#667085"),
        )
    )

    metrics = report_metrics(df)
    state_counts = contact_state_counts(df)
    progress_rate = contact_progress_rate(df)

    story = []

    logo_path = Path(CMA_LOGO_PATH)
    if logo_path.exists():
        logo = Image(str(logo_path))
        logo.drawHeight = 3.35 * cm
        logo.drawWidth = 13.4 * cm
        logo.hAlign = "CENTER"
        story.append(Spacer(1, 0.8 * cm))
        story.append(logo)
    else:
        story.append(Spacer(1, 1.0 * cm))
        story.append(
            Paragraph(
                "CMA Nouvelle-Aquitaine",
                styles["ReportTitle"],
            )
        )

    story.extend(
        [
            Spacer(1, 1.25 * cm),
            Table(
                [["RAPPORT CELLULE DE CRISE"]],
                colWidths=[18.5 * cm],
                rowHeights=[1.55 * cm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(CMA_RED)),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 22),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BOX", (0, 0), (-1, -1), 0, colors.HexColor(CMA_RED)),
                    ]
                ),
                hAlign="CENTER",
            ),
            Spacer(1, 0.55 * cm),
            Paragraph(
                "Cartographie et bilan des entreprises appelées",
                ParagraphStyle(
                    name="CoverSubtitleV5",
                    parent=styles["Heading2"],
                    fontName="Helvetica-Bold",
                    fontSize=17,
                    leading=21,
                    textColor=colors.HexColor("#172033"),
                    alignment=TA_CENTER,
                ),
            ),
            Spacer(1, 1.1 * cm),
            Paragraph(
                f"Date de l’export : {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
                ParagraphStyle(
                    name="ExportDate",
                    parent=styles["BodyText"],
                    fontName="Helvetica",
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor("#667085"),
                    alignment=TA_CENTER,
                ),
            ),
            PageBreak(),
        ]
    )


    metric_data = [
        [
            Paragraph("<b>Entreprises appelées</b>", styles["SmallMuted"]),
            Paragraph("<b>Contactées</b>", styles["SmallMuted"]),
            Paragraph("<b>Message vocal & mail</b>", styles["SmallMuted"]),
            Paragraph("<b>Mauvais numéros</b>", styles["SmallMuted"]),
            Paragraph("<b>Déjà contactées</b>", styles["SmallMuted"]),
            Paragraph("<b>Avancement</b>", styles["SmallMuted"]),
        ],
        [
            str(metrics["total"]),
            str(state_counts["Entreprise contactée"]),
            str(state_counts["Message vocal & mail envoyé"]),
            str(state_counts["Mauvais numéro"]),
            str(state_counts["Déjà contactée"]),
            f"{progress_rate} %",
        ],
    ]

    metric_table = Table(
        metric_data,
        colWidths=[4.2 * cm] * 6,
        rowHeights=[0.8 * cm, 1.15 * cm],
    )
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F7")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D0D5DD")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E7EC")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 17),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#172033")),
            ]
        )
    )
    story.extend([metric_table, Spacer(1, 0.35 * cm)])

    story.append(
        Paragraph(
            "Cartographie du périmètre filtré",
            styles["SectionTitleCMA"],
        )
    )
    story.append(
        Paragraph(
            report_scope_text(df),
            styles["SmallMuted"],
        )
    )
    story.append(Spacer(1, 0.2 * cm))

    map_bytes, excluded_points = create_osm_report_map(df)
    if map_bytes is not None:
        map_image = Image(BytesIO(map_bytes))
        map_image.drawWidth = 25.2 * cm
        map_image.drawHeight = 15.1 * cm
        map_image.hAlign = "CENTER"
        story.append(map_image)
    else:
        story.append(create_fallback_report_map(df))

    if excluded_points:
        story.append(Spacer(1, 0.12 * cm))
        story.append(
            Paragraph(
                f"{excluded_points} point(s) géographiques aberrant(s) ou hors emprise "
                "ont été exclus du cadrage de la carte.",
                styles["SmallMuted"],
            )
        )

    story.append(
        Paragraph(
            "Fond cartographique © contributeurs OpenStreetMap.",
            styles["SmallMuted"],
        )
    )
    story.append(PageBreak())

    story.append(
        Paragraph(
            "Analyse statistique",
            styles["SectionTitleCMA"],
        )
    )

    epci_series = (
        df.groupby("EPCI / CDC").size()
        if not df.empty
        else pd.Series(dtype=int)
    )
    commune_series = (
        df.groupby("Commune").size()
        if not df.empty
        else pd.Series(dtype=int)
    )
    contact_series = (
        df.groupby("État du contact").size()
        if not df.empty
        else pd.Series(dtype=int)
    )
    theme_series = (
        df.groupby("Thématique").size()
        if not df.empty
        else pd.Series(dtype=int)
    )

    charts_table = Table(
        [
            [
                create_horizontal_bar_chart(
                    contact_series,
                    "État des contacts",
                ),
                create_horizontal_bar_chart(
                    epci_series,
                    "Répartition par CDC / EPCI",
                ),
            ],
            [
                create_horizontal_bar_chart(
                    commune_series,
                    "Principales communes",
                ),
                create_horizontal_bar_chart(
                    theme_series,
                    "Thématiques des commentaires",
                ),
            ],
        ],
        colWidths=[12.5 * cm, 12.5 * cm],
        hAlign="CENTER",
    )
    charts_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(charts_table)
    story.append(PageBreak())
    story.append(create_daily_calls_chart(df))
    story.append(Spacer(1, 0.35 * cm))
    story.append(
        Paragraph(
            "Précaution RGPD : le rapport reprend uniquement les informations "
            "présentes dans le fichier importé et les critères actuellement sélectionnés.",
            styles["SmallMuted"],
        )
    )



    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()



def create_html_report(df: pd.DataFrame) -> bytes:
    metrics = report_metrics(df)

    by_contact_state = (
        df.groupby("État du contact")
        .size()
        .sort_values(ascending=False)
        .to_dict()
        if not df.empty
        else {}
    )
    progress_rate = contact_progress_rate(df)

    by_epci = (
        df.groupby("EPCI / CDC")
        .size()
        .sort_values(ascending=False)
        .to_dict()
        if not df.empty
        else {}
    )
    by_commune = (
        df.groupby("Commune")
        .size()
        .sort_values(ascending=False)
        .head(15)
        .to_dict()
        if not df.empty
        else {}
    )
    by_theme = (
        df.groupby("Thématique")
        .size()
        .sort_values(ascending=False)
        .to_dict()
        if not df.empty
        else {}
    )

    def list_items(data: dict[str, Any]) -> str:
        return "".join(
            f"<li><strong>{html.escape(str(key))}</strong> : {value}</li>"
            for key, value in data.items()
        ) or "<li>Aucune donnée</li>"

    generated_at = datetime.now().strftime("%d/%m/%Y à %H:%M")

    report = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport cellule de crise CMA</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 38px;
    color: #172033;
}}
header {{
    padding: 24px;
    color: white;
    background: #111827;
    border-left: 8px solid #D71920;
}}
h1 {{ margin: 0; font-size: 28px; }}
.subtitle {{ margin-top: 8px; color: #E5E7EB; }}
.metrics {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 24px 0;
}}
.metric {{
    padding: 16px;
    border: 1px solid #E3E7ED;
    border-radius: 12px;
}}
.metric strong {{
    display: block;
    font-size: 28px;
}}
section {{
    margin-top: 28px;
}}
h2 {{
    padding-bottom: 7px;
    border-bottom: 2px solid #D71920;
}}
li {{ margin-bottom: 7px; }}
.note {{
    margin-top: 30px;
    padding: 14px;
    background: #FFF5F5;
    border-left: 4px solid #D71920;
}}
footer {{
    margin-top: 40px;
    color: #667085;
    font-size: 12px;
}}
@media print {{
    body {{ margin: 18mm; }}
}}
</style>
</head>
<body>
<header>
    <h1>Rapport de la cellule de crise — Entreprises appelées</h1>
    <div class="subtitle">Période du {metrics['first_date']} au {metrics['last_date']}</div>
</header>

<div class="metrics">
    <div class="metric"><strong>{metrics['total']}</strong>entreprises appelées</div>
    <div class="metric"><strong>{metrics['communes']}</strong>communes concernées</div>
    <div class="metric"><strong>{metrics['epci']}</strong>CDC / EPCI concernés</div>
    <div class="metric"><strong>{metrics['localized']}</strong>entreprises localisées</div>
</div>

<section>
    <h2>État de la campagne d'appels</h2>
    <p><strong>Avancement estimé :</strong> {progress_rate} %</p>
    <ul>{list_items(by_contact_state)}</ul>
</section>

<section>
    <h2>Répartition par CDC / EPCI</h2>
    <ul>{list_items(by_epci)}</ul>
</section>

<section>
    <h2>Principales communes</h2>
    <ul>{list_items(by_commune)}</ul>
</section>

<section>
    <h2>Principales thématiques issues des commentaires</h2>
    <ul>{list_items(by_theme)}</ul>
</section>

<div class="note">
    <strong>Précaution d'utilisation :</strong>
    cette restitution est produite à partir des données importées dans l'application.
    Les commentaires doivent rester factuels et ne contenir que les informations
    strictement nécessaires au suivi de la crise.
</div>

<footer>
    Rapport généré le {generated_at} — CMA Nouvelle-Aquitaine
</footer>
</body>
</html>
"""
    return report.encode("utf-8")


# ============================================================
# SIDEBAR
# ============================================================

def sync_page_from_navigation() -> None:
    st.session_state.current_page = st.session_state.nav_radio


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">🔥 CMA<br>Cellule de crise</div>
                <div class="sidebar-brand-subtitle">
                    Cartographie, pilotage territorial et restitution des entreprises appelées.
                </div>
                <div class="sidebar-red-line"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pages = [
            "Tableau de bord",
            "Importer les appels",
            "Cartographie",
            "Rapport cellule de crise",
            "Identification Lège-Cap-Ferret",
        ]
        icons = {
            "Tableau de bord": "🏠",
            "Importer les appels": "📥",
            "Cartographie": "🗺️",
            "Rapport cellule de crise": "📊",
            "Identification Lège-Cap-Ferret": "📍",
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

        st.divider()
        current_data = st.session_state.crisis_data
        st.caption("SESSION ACTIVE")
        st.markdown(
            f"""
            <div style="padding:.85rem;border:1px solid rgba(255,255,255,.12);
                        border-radius:13px;background:rgba(255,255,255,.055)">
                <div style="font-size:.73rem;color:rgba(255,255,255,.58)">Entreprises chargées</div>
                <div style="margin-top:.18rem;font-size:1.2rem;font-weight:850">{len(current_data)}</div>
                <div style="margin-top:.7rem;font-size:.73rem;color:rgba(255,255,255,.58)">Persistance</div>
                <div style="margin-top:.18rem;font-size:.82rem;font-weight:700">Session uniquement</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "Les adresses sont envoyées au géocodeur public uniquement lors du traitement."
        )

    return st.session_state.nav_radio


# ============================================================
# PAGES PRINCIPALES
# ============================================================

def page_import() -> None:
    render_header(
        "Importer les entreprises appelées",
        "Chargez le nom de l'entreprise, son adresse, sa commune, la date de l'appel, l'état du contact et un commentaire factuel.",
        "Préparation des données",
    )

    st.warning(
        "RGPD : n'importez pas de données personnelles inutiles. "
        "Les adresses sont transmises au service public de géocodage pour obtenir les coordonnées."
    )

    left, right = st.columns([1, 1.6], gap="large")

    with left:
        render_section_title("Fichier attendu", "Excel ou CSV, avec six colonnes obligatoires.")

        st.code(
            "Nom de l'entreprise | Adresse | Commune | Date de l'appel | État du contact | Commentaire"
        )

        st.download_button(
            "Télécharger le modèle Excel",
            data=create_crisis_excel_template(),
            file_name="modele_entreprises_appelees.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        uploaded = st.file_uploader(
            "Déposer le fichier",
            type=["xlsx", "xls", "csv"],
            key="crisis_file_import",
        )

    with right:
        if uploaded is None:
            st.info("Déposez le fichier pour afficher un aperçu avant géocodage.")
            return

        preview, warnings = read_uploaded_file(uploaded)

        for warning in warnings:
            st.warning(warning)

        if preview is None:
            return

        render_section_title(
            f"Aperçu — {len(preview)} entreprise(s)",
            "Vérifiez les colonnes avant de lancer le traitement.",
        )
        display_preview = preview.copy()
        display_preview["Date de l'appel"] = pd.to_datetime(
            display_preview["Date de l'appel"],
            errors="coerce",
        ).dt.strftime("%d/%m/%Y")
        st.dataframe(display_preview, use_container_width=True, hide_index=True, height=390)

        if st.button(
            "Géocoder et charger les entreprises",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Géocodage et rattachement aux CDC / EPCI…"):
                st.session_state.crisis_data = enrich_dataframe(preview)
            st.success("Les entreprises ont été chargées.")
            st.rerun()

    render_footer()


def page_dashboard() -> None:
    render_header(
        APP_NAME,
        "Vue consolidée des appels réalisés, des territoires concernés et des principales difficultés exprimées.",
        "Pilotage",
    )

    df = st.session_state.crisis_data
    if df.empty:
        st.info(
            "Aucune donnée chargée. Utilisez l'onglet « Importer les appels » pour commencer."
        )
        return

    filtered = render_filters(df, "dashboard")
    metrics = report_metrics(filtered)
    state_counts = contact_state_counts(filtered)
    progress_rate = contact_progress_rate(filtered)

    cols = st.columns(6)
    with cols[0]:
        render_metric("Entreprises appelées", metrics["total"], "Après application des filtres")
    with cols[1]:
        render_metric(
            "Entreprises contactées",
            state_counts["Entreprise contactée"],
            "Échange direct réalisé",
        )
    with cols[2]:
        render_metric(
            "Message vocal & mail",
            state_counts["Message vocal & mail envoyé"],
            "Relance ou retour potentiel",
        )
    with cols[3]:
        render_metric(
            "Mauvais numéros",
            state_counts["Mauvais numéro"],
            "Coordonnée téléphonique inutilisable",
        )
    with cols[4]:
        render_metric(
            "Déjà contactées",
            state_counts["Déjà contactée"],
            "Entreprise déjà prise en charge",
        )
    with cols[5]:
        render_metric(
            "Avancement",
            f"{progress_rate} %",
            "Traitements considérés comme terminés",
        )

    st.write("")
    map_col, chart_col = st.columns([2.15, 1], gap="large")

    with map_col:
        st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
        render_section_title(
            "Cartographie opérationnelle",
            "Le commentaire apparaît au survol de chaque point.",
        )
        render_contact_state_legend([state for state in CONTACT_STATES if state in set(filtered["État du contact"].dropna().unique())])
        render_crisis_map(filtered, height=610, heatmap=False)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col:
        epci_counts = (
            filtered.groupby("EPCI / CDC")
            .size()
            .reset_index(name="Entreprises")
            .sort_values("Entreprises")
        )
        fig = px.bar(
            epci_counts,
            x="Entreprises",
            y="EPCI / CDC",
            orientation="h",
            text="Entreprises",
        )
        fig.update_traces(marker_color=CMA_RED, textposition="outside")
        fig.update_layout(
            height=320,
            margin=dict(l=5, r=30, t=45, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="",
            title="Appels par CDC / EPCI",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        contact_counts = (
            filtered.groupby("État du contact")
            .size()
            .reset_index(name="Entreprises")
        )
        fig = px.pie(
            contact_counts,
            names="État du contact",
            values="Entreprises",
            hole=.62,
            color="État du contact",
            color_discrete_map=CONTACT_STATE_HEX,
        )
        fig.update_layout(
            height=330,
            margin=dict(l=5, r=5, t=45, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            title="État de la campagne d'appels",
            legend=dict(orientation="h", yanchor="top", y=-0.12),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    daily = (
        filtered.dropna(subset=["Date de l'appel"])
        .assign(Jour=lambda x: pd.to_datetime(x["Date de l'appel"]).dt.date)
        .groupby("Jour")
        .size()
        .reset_index(name="Appels")
        .sort_values("Jour")
    )

    if not daily.empty:
        fig = px.line(
            daily,
            x="Jour",
            y="Appels",
            markers=True,
            title="Évolution quotidienne des appels",
        )
        fig.update_traces(line_color=CMA_RED)
        fig.update_layout(
            height=340,
            margin=dict(l=10, r=15, t=50, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="Nombre d'appels",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    render_footer()


def page_map() -> None:
    render_header(
        "Cartographie des entreprises appelées",
        "Explorez les points, les commentaires et les concentrations d'appels par territoire.",
        "Cartographie",
    )

    df = st.session_state.crisis_data
    if df.empty:
        st.info("Importez d'abord un fichier d'entreprises appelées.")
        return

    filtered = render_filters(df, "map")

    c1, c2 = st.columns([1, 3])
    with c1:
        heatmap = st.toggle("Afficher la carte de chaleur", value=False)
        st.metric("Entreprises affichées", len(filtered))
        st.metric("Points géolocalisés", int(filtered["Latitude"].notna().sum()))

        st.download_button(
            "Exporter les données filtrées",
            data=create_results_excel(filtered),
            file_name="entreprises_appelees_filtrees.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c2:
        render_contact_state_legend([state for state in CONTACT_STATES if state in set(filtered["État du contact"].dropna().unique())])
        render_crisis_map(filtered, height=735, heatmap=heatmap)

    render_section_title(
        "Tableau de contrôle",
        "Utilisez-le pour repérer les adresses à vérifier avant le rapport final.",
    )
    control_columns = [
        "Nom de l'entreprise",
        "Adresse",
        "Commune",
        "Date de l'appel",
        "État du contact",
        "EPCI / CDC",
        "Grand territoire",
        "Thématique",
        "Commentaire",
        "Statut géocodage",
        "Adresse reconnue",
    ]
    display = filtered[control_columns].copy()
    display["Date de l'appel"] = pd.to_datetime(
        display["Date de l'appel"],
        errors="coerce",
    ).dt.strftime("%d/%m/%Y")
    st.dataframe(display, use_container_width=True, hide_index=True, height=420)

    render_footer()


def page_report() -> None:
    render_header(
        "Rapport de la cellule de crise",
        "Préparez une restitution territoriale, chronologique et thématique à partir des entreprises appelées.",
        "Restitution",
    )

    df = st.session_state.crisis_data
    if df.empty:
        st.info("Importez d'abord les entreprises appelées.")
        return

    filtered = render_filters(df, "report")
    metrics = report_metrics(filtered)

    state_counts = contact_state_counts(filtered)
    progress_rate = contact_progress_rate(filtered)

    cols = st.columns(6)
    with cols[0]:
        render_metric("Entreprises appelées", metrics["total"], f"Du {metrics['first_date']} au {metrics['last_date']}")
    with cols[1]:
        render_metric("Contactées", state_counts["Entreprise contactée"], "Échange direct réalisé")
    with cols[2]:
        render_metric("Message vocal & mail", state_counts["Message vocal & mail envoyé"], "Retour potentiel")
    with cols[3]:
        render_metric("Mauvais numéros", state_counts["Mauvais numéro"], "Coordonnées à corriger")
    with cols[4]:
        render_metric("Déjà contactées", state_counts["Déjà contactée"], "Traitement déjà réalisé")
    with cols[5]:
        render_metric("Avancement", f"{progress_rate} %", "Campagne considérée comme traitée")

    st.write("")
    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        contact_counts = (
            filtered.groupby("État du contact")
            .size()
            .reset_index(name="Entreprises")
            .sort_values("Entreprises", ascending=False)
        )
        st.caption("Répartition par état du contact")
        st.dataframe(contact_counts, use_container_width=True, hide_index=True)

    with c2:
        epci_counts = (
            filtered.groupby("EPCI / CDC")
            .size()
            .reset_index(name="Entreprises")
            .sort_values("Entreprises", ascending=False)
        )
        st.caption("Répartition par CDC / EPCI")
        st.dataframe(epci_counts, use_container_width=True, hide_index=True)

    with c3:
        theme_counts = (
            filtered.groupby("Thématique")
            .size()
            .reset_index(name="Entreprises")
            .sort_values("Entreprises", ascending=False)
        )
        st.caption("Thématiques des commentaires")
        st.dataframe(theme_counts, use_container_width=True, hide_index=True)

    render_section_title(
        "Carte de restitution",
        "La carte reprend exactement le périmètre défini par les filtres.",
    )
    render_crisis_map(filtered, height=620, heatmap=False)

    render_section_title(
        "Exports du rapport",
        "Le PDF reprend automatiquement les critères actifs et la cartographie filtrée.",
    )

    export_cols = st.columns(2)
    with export_cols[0]:
        st.download_button(
            "Télécharger les données du rapport",
            data=create_results_excel(filtered),
            file_name="rapport_cellule_crise_donnees.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with export_cols[1]:
        st.download_button(
            "Générer et télécharger le rapport PDF",
            data=create_pdf_report(filtered),
            file_name="rapport_cellule_crise.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    render_footer()


# ============================================================
# ONGLET LÈGE / CAP-FERRET
# ============================================================

def create_lege_excel_template() -> bytes:
    template = pd.DataFrame(
        [
            {
                "Nom": "Entreprise exemple",
                "Adresse": "1 avenue de la Mairie, 33950 Lège-Cap-Ferret",
            }
        ]
    )
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        template.to_excel(writer, index=False, sheet_name="Adresses")
    return buffer.getvalue()


def classify_lege_cap_ferret_sector_from_coordinates(
    latitude: float,
    longitude: float,
) -> tuple[str, str]:
    ax = TRUC_VERT_POINT["longitude"]
    ay = TRUC_VERT_POINT["latitude"]
    bx = POINTE_AUX_CHEVAUX_POINT["longitude"]
    by = POINTE_AUX_CHEVAUX_POINT["latitude"]

    cross_product = (
        (bx - ax) * (latitude - ay)
        - (by - ay) * (longitude - ax)
    )

    tolerance = 0.000035

    if abs(cross_product) <= tolerance:
        return "À vérifier", "Proche de la limite historique"
    if cross_product > 0:
        return "Lège", "Au nord de la limite historique"
    return "Cap-Ferret", "Au sud de la limite historique"


def read_lege_file(uploaded_file) -> tuple[pd.DataFrame | None, list[str]]:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=None, engine="python", dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)
    except Exception as exc:
        return None, [f"Impossible de lire le fichier : {exc}"]

    normalized = {
        normalize_place(column): column
        for column in df.columns
    }

    name_col = next(
        (
            normalized[key]
            for key in ["nom", "nom entreprise", "entreprise", "raison sociale"]
            if key in normalized
        ),
        None,
    )
    address_col = next(
        (
            normalized[key]
            for key in ["adresse", "adresse complete", "adresse postale"]
            if key in normalized
        ),
        None,
    )

    if name_col is None or address_col is None:
        return None, ["Le fichier doit contenir les colonnes Nom et Adresse."]

    clean = df[[name_col, address_col]].copy()
    clean.columns = ["Nom", "Adresse"]
    clean["Nom"] = clean["Nom"].fillna("").astype(str).str.strip()
    clean["Adresse"] = clean["Adresse"].fillna("").astype(str).str.strip()
    clean = clean[
        clean["Nom"].ne("") & clean["Adresse"].ne("")
    ].drop_duplicates().reset_index(drop=True)

    return clean, []


@st.cache_data(show_spinner=False, ttl=86400)
def geocode_lege_address(address: str) -> dict[str, Any]:
    result = geocode_address(address, "Lège-Cap-Ferret")

    if "Latitude" not in result or "Longitude" not in result:
        return result

    sector, location = classify_lege_cap_ferret_sector_from_coordinates(
        float(result["Latitude"]),
        float(result["Longitude"]),
    )
    result["Secteur"] = sector
    result["Localité détectée"] = location
    return result


def geocode_lege_dataframe(source_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    progress = st.progress(0)
    total = len(source_df)

    for position, (_, row) in enumerate(source_df.iterrows(), start=1):
        rows.append(
            {
                "Nom": row["Nom"],
                "Adresse saisie": row["Adresse"],
                **geocode_lege_address(row["Adresse"]),
            }
        )
        progress.progress(position / total)

    progress.empty()
    return pd.DataFrame(rows)


def render_lege_map(df: pd.DataFrame) -> None:
    valid = df.dropna(subset=["Latitude", "Longitude"]).copy()
    if valid.empty:
        st.info("Aucun point exploitable.")
        return

    valid["Couleur"] = valid["Secteur"].map(
        {
            "Lège": [38, 113, 221, 225],
            "Cap-Ferret": [215, 25, 32, 225],
            "À vérifier": [241, 145, 0, 225],
        }
    )

    lege_polygon_df = pd.DataFrame([{"polygon": LEGE_SECTOR_POLYGON}])
    cap_polygon_df = pd.DataFrame([{"polygon": CAP_FERRET_SECTOR_POLYGON}])
    boundary_df = pd.DataFrame(
        [
            {
                "from": [TRUC_VERT_POINT["longitude"], TRUC_VERT_POINT["latitude"]],
                "to": [
                    POINTE_AUX_CHEVAUX_POINT["longitude"],
                    POINTE_AUX_CHEVAUX_POINT["latitude"],
                ],
            }
        ]
    )

    layers = [
        pdk.Layer(
            "PolygonLayer",
            data=lege_polygon_df,
            get_polygon="polygon",
            get_fill_color=[38, 113, 221, 28],
            get_line_color=[38, 113, 221, 110],
            line_width_min_pixels=1,
            stroked=True,
            filled=True,
        ),
        pdk.Layer(
            "PolygonLayer",
            data=cap_polygon_df,
            get_polygon="polygon",
            get_fill_color=[215, 25, 32, 28],
            get_line_color=[215, 25, 32, 110],
            line_width_min_pixels=1,
            stroked=True,
            filled=True,
        ),
        pdk.Layer(
            "LineLayer",
            data=boundary_df,
            get_source_position="from",
            get_target_position="to",
            get_color=[102, 112, 133, 220],
            get_width=5,
            width_min_pixels=3,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=valid,
            get_position="[Longitude, Latitude]",
            get_fill_color="Couleur",
            get_line_color=[255, 255, 255, 245],
            get_radius=95,
            radius_min_pixels=7,
            radius_max_pixels=16,
            line_width_min_pixels=2,
            pickable=True,
            stroked=True,
            filled=True,
        ),
    ]

    deck = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=LEGE_CENTER_LAT,
            longitude=LEGE_CENTER_LON,
            zoom=LEGE_DEFAULT_ZOOM,
            pitch=0,
        ),
        layers=layers,
        tooltip={
            "html": """
                <div style="min-width:270px;font-family:Arial,sans-serif">
                    <div style="font-size:15px;font-weight:800;margin-bottom:7px">{Nom}</div>
                    <div><b>Adresse :</b> {Adresse saisie}</div>
                    <div><b>Secteur :</b> {Secteur}</div>
                    <div><b>Résultat :</b> {Statut géocodage}</div>
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
    st.pydeck_chart(deck, height=680, use_container_width=True)


def page_lege_identification() -> None:
    render_header(
        "Identification Lège / Cap-Ferret",
        "Outil conservé à part : géocodage d'adresses et séparation opérationnelle entre les deux secteurs.",
        "Outil spécifique",
    )

    st.info(
        "Cet onglet reste indépendant de la cartographie générale de la cellule de crise."
    )

    left, right = st.columns([1, 1.8], gap="large")

    with left:
        st.download_button(
            "Télécharger le modèle",
            data=create_lege_excel_template(),
            file_name="modele_lege_cap_ferret.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        uploaded = st.file_uploader(
            "Importer Nom + Adresse",
            type=["xlsx", "xls", "csv"],
            key="lege_import",
        )

        if uploaded is not None:
            preview, errors = read_lege_file(uploaded)
            for error in errors:
                st.warning(error)

            if preview is not None:
                st.dataframe(preview, use_container_width=True, hide_index=True)
                if st.button(
                    "Géocoder les adresses",
                    type="primary",
                    use_container_width=True,
                    key="lege_geocode",
                ):
                    st.session_state.lege_data = geocode_lege_dataframe(preview)
                    st.rerun()

        if not st.session_state.lege_data.empty:
            if st.button(
                "Effacer les données de cet onglet",
                use_container_width=True,
            ):
                st.session_state.lege_data = pd.DataFrame()
                st.rerun()

    with right:
        result = st.session_state.lege_data

        if result.empty:
            st.info("Importez les adresses pour afficher la carte.")
        else:
            sectors = st.multiselect(
                "Afficher les secteurs",
                ["Lège", "Cap-Ferret", "À vérifier"],
                default=["Lège", "Cap-Ferret", "À vérifier"],
            )
            filtered = result[result["Secteur"].isin(sectors)].copy()
            render_lege_map(filtered)

    if not st.session_state.lege_data.empty:
        result = st.session_state.lege_data

        render_section_title("Exports séparés", "Téléchargez chaque secteur indépendamment.")

        c1, c2, c3 = st.columns(3)
        lege = result[result["Secteur"] == "Lège"]
        cap = result[result["Secteur"] == "Cap-Ferret"]
        verify = result[result["Secteur"] == "À vérifier"]

        with c1:
            st.download_button(
                f"Extraire Lège ({len(lege)})",
                data=create_results_excel(lege),
                file_name="entreprises_lege.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                disabled=lege.empty,
            )
        with c2:
            st.download_button(
                f"Extraire Cap-Ferret ({len(cap)})",
                data=create_results_excel(cap),
                file_name="entreprises_cap_ferret.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                disabled=cap.empty,
            )
        with c3:
            st.download_button(
                f"Extraire à vérifier ({len(verify)})",
                data=create_results_excel(verify),
                file_name="entreprises_a_verifier.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                disabled=verify.empty,
            )

        st.dataframe(result, use_container_width=True, hide_index=True, height=360)

    render_footer()


# ============================================================
# APPLICATION
# ============================================================

def main() -> None:
    inject_css()
    initialize_state()
    page = render_sidebar()

    if page == "Tableau de bord":
        page_dashboard()
    elif page == "Importer les appels":
        page_import()
    elif page == "Cartographie":
        page_map()
    elif page == "Rapport cellule de crise":
        page_report()
    elif page == "Identification Lège-Cap-Ferret":
        page_lege_identification()


if __name__ == "__main__":
    main()
