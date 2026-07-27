from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="VACUNACION Plataforma Digital",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "VACUNACION Plataforma Digital"
DEVELOPER = "EGS | Estudio de Gestión de Sistemas"
LAST_REVIEW = "27/07/2026"

MEDICAL_NOTICE = (
    "La plataforma brinda información general y no reemplaza la consulta profesional, "
    "la revisión del carnet ni la indicación de un equipo de salud."
)

if "section" not in st.session_state:
    st.session_state.section = "Inicio"

if "search_history" not in st.session_state:
    st.session_state.search_history = []


# =========================================================
# MODELOS
# =========================================================

@dataclass(frozen=True)
class OfficialSource:
    name: str
    jurisdiction: str
    description: str
    url: str
    reviewed_at: str
    status: str = "Verificada"


@dataclass(frozen=True)
class VaccinationCenter:
    name: str
    address: str
    locality: str
    phone: str
    source: str
    service_note: str
    verified_at: str
    status: str = "Verificar disponibilidad antes de asistir"


@dataclass(frozen=True)
class VaccineCard:
    name: str
    stage: str
    protects: str
    audience: str
    summary: str
    schedule: str
    special: str
    contraindications: str
    adverse_effects: str
    source_name: str
    source_url: str
    reviewed_at: str
    status: str = "Contenido orientativo con fuente oficial"


# =========================================================
# FUENTES OFICIALES
# =========================================================

OFFICIAL_SOURCES: List[OfficialSource] = [
    OfficialSource(
        name="Calendario Nacional de Vacunación 2026",
        jurisdiction="Ministerio de Salud de la Nación",
        description=(
            "Calendario oficial por etapas de la vida, situaciones especiales "
            "y grupos específicos."
        ),
        url="https://www.argentina.gob.ar/salud/vacunas",
        reviewed_at=LAST_REVIEW,
    ),
    OfficialSource(
        name="Resolución 339/2026",
        jurisdiction="Boletín Oficial de la República Argentina",
        description=(
            "Modificación oficial del esquema de vacuna triple viral: "
            "primera dosis a los 12 meses y segunda entre los 15 y 18 meses, "
            "con reglas transitorias para determinadas cohortes."
        ),
        url=(
            "https://www.argentina.gob.ar/normativa/nacional/"
            "resoluci%C3%B3n-339-2026-423397/texto"
        ),
        reviewed_at=LAST_REVIEW,
    ),
    OfficialSource(
        name="Centros de vacunación de Córdoba",
        jurisdiction="Gobierno de la Provincia de Córdoba",
        description=(
            "Conjunto oficial de datos sobre centros de vacunación de la provincia."
        ),
        url=(
            "https://datosgestionabierta.cba.gov.ar/dataset/"
            "centros-de-vacunacion-de-la-provincia-de-cordoba"
        ),
        reviewed_at=LAST_REVIEW,
    ),
    OfficialSource(
        name="CAPS de San Francisco",
        jurisdiction="Municipalidad de San Francisco",
        description=(
            "Red municipal de Centros de Atención Primaria de la Salud y datos de contacto."
        ),
        url=(
            "https://www.sanfrancisco.gov.ar/contenidos/"
            "centro-de-atencion-primaria-de-salud-caps-282"
        ),
        reviewed_at=LAST_REVIEW,
    ),
    OfficialSource(
        name="Campaña antigripal 2026 en San Francisco",
        jurisdiction="Municipalidad de San Francisco",
        description=(
            "Información municipal sobre la campaña antigripal 2026, "
            "Asistencia Pública y CAPS participantes."
        ),
        url=(
            "https://www.sanfrancisco.gov.ar/noticia/"
            "municipio-comienza-con-la-campana-de-vacunacion-antigripal-2026-6732"
        ),
        reviewed_at=LAST_REVIEW,
    ),
    OfficialSource(
        name="Inmunizaciones en Argentina",
        jurisdiction="OPS/OMS",
        description=(
            "Materiales técnicos y de comunicación sobre inmunizaciones en Argentina."
        ),
        url="https://www.paho.org/es/inmunizaciones-argentina",
        reviewed_at=LAST_REVIEW,
    ),
]


# =========================================================
# CENTROS MUNICIPALES VERIFICADOS EN FUENTE OFICIAL
# =========================================================

CENTERS: List[VaccinationCenter] = [
    VaccinationCenter(
        name="Asistencia Pública",
        address="Colón 165",
        locality="San Francisco",
        phone="03564 439154",
        source="Municipalidad de San Francisco",
        service_note=(
            "La campaña antigripal 2026 informó atención de lunes a viernes "
            "de 7:00 a 12:30 y de 14:00 a 19:00. Verificar vigencia antes de asistir."
        ),
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS Cottolengo",
        address="José Hernández 3049",
        locality="San Francisco",
        phone="03564 434726 / 3564 213014",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS Roque Sáenz Peña",
        address="Falucho esq. Gerónimo del Barco",
        locality="San Francisco",
        phone="3564 370400",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS Bouchard",
        address="Rioja esq. General Paz",
        locality="San Francisco",
        phone="03564 498404",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS La Milka",
        address="Madre Marcilla 407",
        locality="San Francisco",
        phone="3564 237775",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS Sarmiento",
        address="Olegario Andrade 707",
        locality="San Francisco",
        phone="03564 498116 / 3564 333452",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS Parque",
        address="Resistencia 578",
        locality="San Francisco",
        phone="03564 434725 / 3564 595398",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS San Cayetano",
        address="Pascual Bailón Sosa 1759",
        locality="San Francisco",
        phone="03564 435274",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
    VaccinationCenter(
        name="CAPS Plaza San Francisco",
        address="Víctor Angelli 4136",
        locality="San Francisco",
        phone="3564 684355",
        source="Municipalidad de San Francisco",
        service_note="Consultar por la mañana el horario de vacunación disponible.",
        verified_at=LAST_REVIEW,
    ),
]


# =========================================================
# CONTENIDO CONECTADO A FUENTE OFICIAL
# =========================================================

VACCINES: List[VaccineCard] = [
    VaccineCard(
        name="Triple viral",
        stage="Infancia",
        protects="Sarampión, rubéola y paperas.",
        audience=(
            "Personas incluidas en el Calendario Nacional y personas con esquemas "
            "incompletos, según evaluación del equipo de salud."
        ),
        summary=(
            "La Resolución 339/2026 estableció una primera dosis a los 12 meses "
            "y una segunda dosis entre los 15 y 18 meses."
        ),
        schedule=(
            "Primera dosis: 12 meses. Segunda dosis: entre 15 y 18 meses. "
            "Existen disposiciones transitorias para cohortes nacidas entre 2021 "
            "y el 30 de junio de 2024."
        ),
        special=(
            "En esquemas incompletos corresponde completar según la normativa "
            "y evaluación del vacunatorio."
        ),
        contraindications=(
            "Consultar la ficha oficial y al equipo de salud. No utilizar esta plataforma "
            "para decidir una contraindicación individual."
        ),
        adverse_effects=(
            "La información de seguridad debe verificarse en la fuente oficial "
            "y con el equipo de salud."
        ),
        source_name="Resolución 339/2026",
        source_url=(
            "https://www.argentina.gob.ar/normativa/nacional/"
            "resoluci%C3%B3n-339-2026-423397/texto"
        ),
        reviewed_at=LAST_REVIEW,
    ),
    VaccineCard(
        name="Vacuna antigripal 2026",
        stage="Situaciones especiales",
        protects="Influenza y sus posibles complicaciones.",
        audience=(
            "La campaña nacional 2026 se dirige a la población objetivo definida "
            "por el Calendario Nacional."
        ),
        summary=(
            "La campaña nacional antigripal 2026 comenzó el 11 de marzo. "
            "La disponibilidad local debe confirmarse antes de asistir."
        ),
        schedule=(
            "Consultar el Calendario Nacional y el vacunatorio para conocer la indicación "
            "según edad, embarazo, factores de riesgo u otras condiciones."
        ),
        special=(
            "En San Francisco la campaña municipal informó atención en Asistencia Pública "
            "y CAPS seleccionados. Los horarios pueden variar."
        ),
        contraindications=(
            "Las contraindicaciones individuales deben evaluarse con un equipo de salud."
        ),
        adverse_effects=(
            "Consultar información oficial y al equipo de salud ante dudas o síntomas."
        ),
        source_name="Ministerio de Salud de la Nación y Municipalidad de San Francisco",
        source_url=(
            "https://www.argentina.gob.ar/noticias/"
            "salud-inicia-la-campana-de-vacunacion-antigripal-en-todo-el-pais"
        ),
        reviewed_at=LAST_REVIEW,
    ),
]

CALENDAR_STAGES: Dict[str, Dict[str, str]] = {
    "Embarazo": {
        "icon": "🤰",
        "kicker": "Antes y durante el embarazo",
        "description": (
            "Acceso directo al calendario oficial y a contenidos específicos "
            "para embarazo."
        ),
    },
    "Recién nacido": {
        "icon": "👶",
        "kicker": "Desde el nacimiento",
        "description": (
            "Información oficial organizada para facilitar la lectura del calendario."
        ),
    },
    "Hasta 1 año": {
        "icon": "🍼",
        "kicker": "Primer año",
        "description": (
            "Etapa oficial del Calendario Nacional de Vacunación 2026."
        ),
    },
    "Hasta 2 años": {
        "icon": "🧒",
        "kicker": "Primera infancia",
        "description": (
            "Etapa oficial del Calendario Nacional de Vacunación 2026."
        ),
    },
    "5 años": {
        "icon": "🎒",
        "kicker": "Ingreso escolar",
        "description": (
            "Etapa oficial del Calendario Nacional de Vacunación 2026."
        ),
    },
    "11 años": {
        "icon": "🧑",
        "kicker": "Adolescencia",
        "description": (
            "Etapa oficial del Calendario Nacional de Vacunación 2026."
        ),
    },
    "15 a 64 años": {
        "icon": "👩",
        "kicker": "Vida adulta",
        "description": (
            "Etapa oficial del Calendario Nacional de Vacunación 2026."
        ),
    },
    "65 años o más": {
        "icon": "👵",
        "kicker": "Personas mayores",
        "description": (
            "Etapa oficial del Calendario Nacional de Vacunación 2026."
        ),
    },
}

INFO_TOPICS = [
    ("🛡️", "Seguridad de las vacunas", "Cómo consultar fuentes oficiales y reportar dudas."),
    ("🤰", "Embarazo", "Acceso a información oficial específica."),
    ("👶", "Vacunación infantil", "Cómo leer el calendario por edad."),
    ("🧑", "Adolescencia", "Información adaptada a esta etapa."),
    ("👵", "Personas mayores", "Consulta de calendario y campañas."),
    ("❤️", "Enfermedades crónicas", "Orientación general y consulta profesional."),
    ("✈️", "Viajes", "Qué revisar antes de viajar."),
    ("🕒", "Esquemas atrasados", "Cómo completar un esquema con el vacunatorio."),
    ("📄", "Pérdida del carnet", "Cómo verificar antecedentes y conservar registros."),
    ("💬", "Mitos y desinformación", "Cómo reconocer una fuente confiable."),
]


# =========================================================
# ESTILOS
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --green:#2C8F78;
        --green-dark:#1F6D5D;
        --green-soft:#EAF7F3;
        --navy:#12304A;
        --blue:#DDF2FA;
        --soft:#F6F9FB;
        --muted:#617486;
        --line:#DDE7EE;
        --white:#FFFFFF;
        --warning:#FFF7DF;
        --shadow:0 18px 50px rgba(18,48,74,.08);
    }

    .stApp { background:var(--white); color:var(--navy); }
    .block-container { max-width:1240px; padding-top:.8rem; padding-bottom:3rem; }
    #MainMenu, footer, header { visibility:hidden; }
    h1,h2,h3 { color:var(--navy); letter-spacing:-.03em; }
    p { line-height:1.65; }

    .topbar {
        display:flex; align-items:center; justify-content:space-between;
        gap:1rem; padding:.9rem 0 1.15rem; border-bottom:1px solid var(--line);
        margin-bottom:1rem;
    }

    .brand {
        font-weight:900; font-size:1.08rem; color:var(--navy);
        letter-spacing:-.02em;
    }

    .brand span { color:var(--green); }

    .top-meta {
        color:var(--muted); font-size:.8rem; font-weight:750;
    }

    .hero {
        padding:4rem 3.2rem; border-radius:32px;
        background:
            radial-gradient(circle at 82% 12%,rgba(221,242,250,.95),transparent 28%),
            radial-gradient(circle at 96% 88%,rgba(234,247,243,.9),transparent 26%),
            linear-gradient(135deg,#F9FCFD 0%,#FFFFFF 60%);
        border:1px solid var(--line); box-shadow:var(--shadow);
        margin-bottom:1.8rem; overflow:hidden;
    }

    .hero-badge {
        display:inline-flex; padding:.48rem .78rem; border-radius:999px;
        background:var(--green-soft); color:var(--green-dark);
        font-weight:850; font-size:.8rem; margin-bottom:1.1rem;
    }

    .hero h1 {
        max-width:860px; font-size:clamp(2.7rem,5.8vw,5.2rem);
        line-height:.96; margin:0 0 1rem;
    }

    .hero p {
        max-width:760px; color:var(--muted); font-size:1.14rem;
        margin-bottom:0;
    }

    .section-header { margin:2.5rem 0 1rem; }

    .section-header span {
        color:var(--green-dark); font-size:.75rem; font-weight:900;
        text-transform:uppercase; letter-spacing:.1em;
    }

    .section-header h2 {
        margin:.35rem 0 .4rem; font-size:2rem;
    }

    .section-header p { color:var(--muted); margin:0; }

    .module-card {
        min-height:220px; padding:1.4rem; border-radius:22px;
        border:1px solid var(--line); background:var(--white); margin-bottom:1rem;
    }

    .module-icon {
        width:48px; height:48px; border-radius:15px; display:grid;
        place-items:center; background:var(--blue); font-size:1.4rem;
        margin-bottom:1rem;
    }

    .module-card p { color:var(--muted); min-height:70px; }

    .stage-card {
        display:grid; grid-template-columns:74px 1fr; gap:1.25rem;
        align-items:center; padding:1.6rem; border:1px solid var(--line);
        border-radius:24px;
        background:linear-gradient(135deg,#FFFFFF 0%,#F5FBFD 100%);
        margin:1.2rem 0;
    }

    .stage-icon {
        width:70px; height:70px; border-radius:20px;
        background:var(--blue); display:grid; place-items:center;
        font-size:2.15rem;
    }

    .stage-kicker {
        color:var(--green-dark); font-size:.72rem; font-weight:900;
        text-transform:uppercase; letter-spacing:.09em;
    }

    .stage-card h2 { margin:.25rem 0 .45rem; }
    .stage-card p { margin:0; color:var(--muted); }

    .notice {
        border-left:4px solid var(--green); background:#F4FBF8;
        padding:1rem 1.1rem; border-radius:12px; margin:1rem 0;
    }

    .warning-box {
        border-left:4px solid #D6A800; background:var(--warning);
        padding:1rem 1.1rem; border-radius:12px; margin:1rem 0;
    }

    .topic-card {
        padding:1.15rem; border:1px solid var(--line);
        border-radius:18px; background:var(--white);
        min-height:180px; margin-bottom:1rem;
    }

    .topic-card .icon { font-size:1.45rem; margin-bottom:.7rem; }
    .topic-card p { color:var(--muted); font-size:.92rem; }

    .source-card {
        padding:1.15rem; border:1px solid var(--line);
        border-radius:18px; background:var(--soft); margin-bottom:1rem;
    }

    .source-card h3 { margin:.2rem 0 .4rem; }
    .source-card p { color:var(--muted); margin:.2rem 0; }
    .source-card a { color:var(--green-dark); font-weight:800; text-decoration:none; }

    .footer {
        margin-top:3rem; border-top:1px solid var(--line);
        padding-top:1.4rem; color:var(--muted); font-size:.85rem;
    }

    @media (max-width:850px) {
        .topbar { align-items:flex-start; flex-direction:column; }
        .hero { padding:2.3rem 1.4rem; border-radius:24px; }
        .stage-card { grid-template-columns:1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# COMPONENTES
# =========================================================

def render_header() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">VACUNACION <span>Plataforma Digital</span></div>
            <div class="top-meta">Información pública · Accesible · Territorial</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        f"""
        <div class="footer">
            <strong>{DEVELOPER}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_navigation() -> None:
    sections = [
        ("Inicio", "🏠"),
        ("Calendario", "📅"),
        ("Orientación", "🧭"),
        ("Vacunas", "💉"),
        ("Información", "📘"),
        ("Dónde vacunarme", "📍"),
        ("Novedades", "🔔"),
        ("Fuentes oficiales", "🔗"),
        ("Administración", "⚙️"),
    ]

    cols = st.columns(3)
    for index, (label, icon) in enumerate(sections):
        with cols[index % 3]:
            if st.button(
                f"{icon} {label}",
                use_container_width=True,
                key=f"nav_{label}",
            ):
                st.session_state.section = label
                st.rerun()


def section_header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-header">
            <span>{kicker}</span>
            <h2>{title}</h2>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_source_link(source: OfficialSource) -> None:
    st.markdown(
        f"""
        <article class="source-card">
            <span class="stage-kicker">{source.jurisdiction}</span>
            <h3>{source.name}</h3>
            <p>{source.description}</p>
            <p><strong>Revisada:</strong> {source.reviewed_at}</p>
            <a href="{source.url}" target="_blank">Abrir fuente oficial ↗</a>
        </article>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PÁGINAS
# =========================================================

def render_home() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-badge">Información pública clara y confiable</div>
            <h1>Todo sobre vacunación, en un solo lugar.</h1>
            <p>
                Consultá el calendario, recibí orientación general, conocé cada vacuna,
                encontrá información útil y accedé a los puntos de vacunación.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Buscar",
        placeholder="Ej.: vacuna antigripal, perdí el carnet, estoy embarazada...",
        key="home_search",
    )

    if query:
        st.session_state.search_history.append(query)
        st.info(
            f"Consulta recibida: “{query}”. Los resultados se limitan a contenido "
            "con fuente oficial cargada."
        )

    section_header(
        "Accesos principales",
        "Elegí qué necesitás consultar",
        "La plataforma organiza la información por necesidad ciudadana.",
    )

    modules = [
        ("📅", "Calendario", "Recorré la vacunación por etapa de vida."),
        ("🧭", "Orientación", "Recibí orientación general basada en reglas."),
        ("💉", "Vacunas", "Consultá fichas claras, trazables y verificables."),
        ("📘", "Información", "Embarazo, viajes, carnet, mitos y más."),
        ("📍", "Dónde vacunarme", "Accedé a centros y datos territoriales."),
        ("🔗", "Fuentes oficiales", "Consultá el origen de cada información."),
    ]

    cols = st.columns(3, gap="large")
    for index, (icon, title, description) in enumerate(modules):
        with cols[index % 3]:
            st.markdown(
                f"""
                <article class="module-card">
                    <div class="module-icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{description}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"Abrir {title}",
                key=f"open_{title}",
                use_container_width=True,
            ):
                st.session_state.section = title
                st.rerun()

    section_header(
        "Actualización",
        "Fuentes conectadas y revisión visible",
        "La plataforma muestra fuente, fecha y estado editorial.",
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Fuentes oficiales conectadas", len(OFFICIAL_SOURCES))
    c2.metric("Centros municipales cargados", len(CENTERS))
    c3.metric("Última revisión general", LAST_REVIEW)


def render_calendar() -> None:
    section_header(
        "Calendario oficial",
        "Calendario de vacunación por etapa de vida",
        "Las etapas se corresponden con la organización del Calendario Nacional 2026.",
    )

    stage = st.segmented_control(
        "Etapa de vida",
        options=list(CALENDAR_STAGES.keys()),
        default="Embarazo",
        label_visibility="collapsed",
    )

    stage_data = CALENDAR_STAGES[stage]

    st.markdown(
        f"""
        <div class="stage-card">
            <div class="stage-icon">{stage_data["icon"]}</div>
            <div>
                <span class="stage-kicker">{stage_data["kicker"]}</span>
                <h2>{stage}</h2>
                <p>{stage_data["description"]}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="notice">
            Consultá el calendario oficial completo para verificar vacunas,
            dosis y situaciones especiales. La plataforma no infiere vacunas faltantes.
        </div>
        """,
        unsafe_allow_html=True,
    )

    official = OFFICIAL_SOURCES[0]
    render_source_link(official)


def render_orientation() -> None:
    section_header(
        "Orientación",
        "¿Qué información podría ser relevante para mí?",
        "Respondé unas preguntas breves para recibir orientación general.",
    )

    st.markdown(
        """
        <div class="notice">
            Según la información ingresada, la plataforma puede priorizar contenidos
            relevantes. No determina vacunas faltantes y siempre recomienda verificar
            el carnet o consultar en un vacunatorio.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("orientation_form"):
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Edad", min_value=0, max_value=120, step=1)
            pregnancy = st.selectbox(
                "¿Cursa un embarazo?",
                ["No corresponde", "No", "Sí"],
            )
            chronic = st.selectbox(
                "¿Tiene alguna enfermedad crónica?",
                ["No sé", "No", "Sí"],
            )

        with col2:
            travel = st.selectbox("¿Tiene un viaje próximo?", ["No", "Sí"])
            card = st.selectbox(
                "¿Tiene disponible su carnet?",
                ["Sí", "No", "No sé"],
            )
            respiratory = st.selectbox(
                "¿Busca información sobre vacunas respiratorias?",
                ["No", "Sí"],
            )

        submitted = st.form_submit_button(
            "Obtener orientación general",
            use_container_width=True,
        )

    if submitted:
        st.markdown(
            f"""
            <div class="notice">
                <strong>Según la información ingresada</strong>, podrían ser relevantes
                contenidos para una persona de {age} años. Verificá tu carnet o consultá
                en un vacunatorio.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if pregnancy == "Sí":
            st.info("Revisá la sección de embarazo del Calendario Nacional.")
        if chronic == "Sí":
            st.info(
                "Consultá a tu equipo de salud por indicaciones vinculadas "
                "a condiciones crónicas."
            )
        if travel == "Sí":
            st.info("Revisá recomendaciones oficiales antes del viaje.")
        if card != "Sí":
            st.info(
                "Consultá en un vacunatorio para verificar antecedentes y completar "
                "la información disponible."
            )
        if respiratory == "Sí":
            st.info(
                "Revisá la información oficial sobre influenza, COVID-19, neumococo "
                "y virus sincicial respiratorio."
            )


def render_vaccines() -> None:
    section_header(
        "Vacunas",
        "Biblioteca con fuentes oficiales",
        "Buscá por vacuna, enfermedad, etapa de vida o situación.",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        query = st.text_input(
            "Buscar",
            key="vaccine_search",
            placeholder="Ej.: triple viral, antigripal...",
        )

    with col2:
        stage_filter = st.selectbox(
            "Filtrar por etapa",
            ["Todas"] + sorted({item.stage for item in VACCINES}),
        )

    results = VACCINES

    if query:
        q = query.lower()
        results = [
            item
            for item in results
            if q in item.name.lower()
            or q in item.protects.lower()
            or q in item.audience.lower()
            or q in item.stage.lower()
            or q in item.summary.lower()
        ]

    if stage_filter != "Todas":
        results = [item for item in results if item.stage == stage_filter]

    if not results:
        st.warning("No se encontraron resultados en el contenido validado cargado.")

    for item in results:
        with st.expander(f"{item.name} · {item.stage}"):
            tabs = st.tabs(
                [
                    "Resumen",
                    "Esquema",
                    "Situaciones especiales",
                    "Seguridad",
                    "Fuente oficial",
                ]
            )

            with tabs[0]:
                st.markdown("### Resumen en un minuto")
                st.write(item.summary)
                st.markdown("### Protege contra")
                st.write(item.protects)
                st.markdown("### Población objetivo")
                st.write(item.audience)

            with tabs[1]:
                st.write(item.schedule)

            with tabs[2]:
                st.write(item.special)

            with tabs[3]:
                st.markdown("#### Contraindicaciones")
                st.write(item.contraindications)
                st.markdown("#### Efectos adversos")
                st.write(item.adverse_effects)

            with tabs[4]:
                st.markdown(
                    f"[Abrir {item.source_name}]({item.source_url})"
                )
                st.caption(
                    f"Estado: {item.status} · Revisión: {item.reviewed_at}"
                )


def render_information() -> None:
    section_header(
        "Información",
        "Información clara para situaciones reales",
        "Explorá temas frecuentes con lenguaje directo y fuentes oficiales.",
    )

    cols = st.columns(3, gap="large")

    for index, (icon, title, description) in enumerate(INFO_TOPICS):
        with cols[index % 3]:
            st.markdown(
                f"""
                <article class="topic-card">
                    <div class="icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{description}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Ver orientación"):
                if title == "Esquemas atrasados":
                    st.write(
                        "No es necesario reiniciar automáticamente un esquema. "
                        "Consultá en un vacunatorio para completar según la normativa vigente."
                    )
                elif title == "Pérdida del carnet":
                    st.write(
                        "Consultá en el vacunatorio o establecimiento donde recibiste las dosis "
                        "y conservá cualquier certificado disponible."
                    )
                else:
                    st.write(
                        "Consultá la información oficial y al equipo de salud para una "
                        "orientación individual."
                    )


def render_centers() -> None:
    section_header(
        "Territorio",
        "Dónde vacunarme en San Francisco",
        "Centros municipales cargados desde fuentes oficiales.",
    )

    st.markdown(
        """
        <div class="warning-box">
            Los servicios y horarios pueden cambiar. Confirmá telefónicamente
            la disponibilidad de vacunas antes de asistir.
        </div>
        """,
        unsafe_allow_html=True,
    )

    search = st.text_input(
        "Buscar por centro o dirección",
        placeholder="Ej.: La Milka, Resistencia, Asistencia Pública...",
    )

    filtered = CENTERS

    if search:
        q = search.lower()
        filtered = [
            center
            for center in CENTERS
            if q in center.name.lower()
            or q in center.address.lower()
            or q in center.locality.lower()
        ]

    if not filtered:
        st.warning("No se encontraron centros con ese criterio.")

    for center in filtered:
        with st.expander(f"{center.name} · {center.address}"):
            st.write(f"**Dirección:** {center.address}")
            st.write(f"**Teléfono:** {center.phone}")
            st.write(f"**Observación:** {center.service_note}")
            st.write(f"**Fuente:** {center.source}")
            st.caption(
                f"Revisión: {center.verified_at} · {center.status}"
            )

            maps_query = quote_plus(
                f"{center.name}, {center.address}, San Francisco, Córdoba, Argentina"
            )
            st.markdown(
                f"[Abrir ubicación en Google Maps]"
                f"(https://www.google.com/maps/search/?api=1&query={maps_query})"
            )

    st.markdown("### Vista resumida")

    centers_df = pd.DataFrame(
        [
            {
                "Centro": center.name,
                "Dirección": center.address,
                "Teléfono": center.phone,
                "Estado": center.status,
            }
            for center in filtered
        ]
    )

    st.dataframe(
        centers_df,
        use_container_width=True,
        hide_index=True,
    )


def render_news() -> None:
    section_header(
        "Novedades",
        "Campañas y anuncios oficiales",
        "Información temporal separada del calendario permanente.",
    )

    st.markdown(
        """
        <div class="source-card">
            <span class="stage-kicker">Campaña 2026</span>
            <h3>Campaña antigripal en San Francisco</h3>
            <p>
                La Municipalidad informó el inicio de la campaña el 11 de marzo de 2026
                en Asistencia Pública y CAPS seleccionados.
            </p>
            <p>
                Esta publicación se conserva como antecedente. Confirmá disponibilidad
                actual antes de asistir.
            </p>
            <a href="https://www.sanfrancisco.gov.ar/noticia/municipio-comienza-con-la-campana-de-vacunacion-antigripal-2026-6732" target="_blank">
                Abrir anuncio municipal ↗
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Flujo editorial"):
        st.code("Borrador → Revisión → Aprobación → Publicación → Archivo")


def render_sources() -> None:
    section_header(
        "Transparencia",
        "Fuentes oficiales",
        "Consultá el origen, jurisdicción y fecha de revisión de la información.",
    )

    for source in OFFICIAL_SOURCES:
        render_source_link(source)


def render_admin() -> None:
    section_header(
        "Administración",
        "Panel de gestión",
        "Control editorial, territorial y analítico de la plataforma.",
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fuentes verificadas", len(OFFICIAL_SOURCES))
    c2.metric("Centros cargados", len(CENTERS))
    c3.metric("Fichas con fuente", len(VACCINES))
    c4.metric("Búsquedas de sesión", len(st.session_state.search_history))

    tabs = st.tabs(
        [
            "Fuentes",
            "Contenidos",
            "Vacunatorios",
            "Analítica",
            "Versionado",
        ]
    )

    with tabs[0]:
        sources_df = pd.DataFrame(
            [
                {
                    "Fuente": source.name,
                    "Jurisdicción": source.jurisdiction,
                    "Estado": source.status,
                    "Revisión": source.reviewed_at,
                }
                for source in OFFICIAL_SOURCES
            ]
        )
        st.dataframe(sources_df, use_container_width=True, hide_index=True)

    with tabs[1]:
        contents_df = pd.DataFrame(
            [
                {
                    "Contenido": item.name,
                    "Etapa": item.stage,
                    "Estado": item.status,
                    "Revisión": item.reviewed_at,
                }
                for item in VACCINES
            ]
        )
        st.dataframe(contents_df, use_container_width=True, hide_index=True)

    with tabs[2]:
        centers_df = pd.DataFrame(
            [
                {
                    "Centro": center.name,
                    "Dirección": center.address,
                    "Estado": center.status,
                    "Revisión": center.verified_at,
                }
                for center in CENTERS
            ]
        )
        st.dataframe(centers_df, use_container_width=True, hide_index=True)

    with tabs[3]:
        if st.session_state.search_history:
            st.write(st.session_state.search_history[-20:])
        else:
            st.info("Todavía no se registraron búsquedas.")

    with tabs[4]:
        st.write(f"Última revisión general: {LAST_REVIEW}")
        st.code("Borrador → Revisión → Aprobación → Publicación → Archivo")


# =========================================================
# ENRUTAMIENTO
# =========================================================

PAGES = {
    "Inicio": render_home,
    "Calendario": render_calendar,
    "Orientación": render_orientation,
    "Vacunas": render_vaccines,
    "Información": render_information,
    "Dónde vacunarme": render_centers,
    "Novedades": render_news,
    "Fuentes oficiales": render_sources,
    "Administración": render_admin,
}

render_header()
render_navigation()
st.divider()

PAGES.get(
    st.session_state.section,
    render_home,
)()

render_footer()
