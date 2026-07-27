from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="VACUNACION Plataforma Digital",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "VACUNACION Plataforma Digital"
DEVELOPER = "EGS | Estudio de Gestión de Sistemas"

MEDICAL_NOTICE = (
    "Información general. No reemplaza la consulta profesional ni permite determinar "
    "si una persona tiene vacunas faltantes."
)


# =========================================================
# ESTILOS
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --green: #2C8F78;
        --green-dark: #1F6D5D;
        --navy: #12304A;
        --blue-soft: #EAF7FB;
        --soft: #F6F9FB;
        --muted: #617486;
        --line: #DDE7EE;
        --white: #FFFFFF;
        --warning: #FFF5D9;
    }

    .stApp {
        background: var(--white);
        color: var(--navy);
    }

    .block-container {
        max-width: 1240px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    h1, h2, h3 {
        color: var(--navy);
        letter-spacing: -0.03em;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: .85rem 0 1.2rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 1.6rem;
    }

    .brand {
        font-weight: 850;
        font-size: 1.05rem;
        color: var(--navy);
    }

    .brand span {
        color: var(--green);
    }

    .status-chip {
        background: var(--blue-soft);
        color: var(--green-dark);
        border-radius: 999px;
        padding: .45rem .7rem;
        font-size: .75rem;
        font-weight: 800;
    }

    .hero {
        padding: 3.2rem 2.6rem;
        border-radius: 28px;
        background:
            radial-gradient(circle at top right, rgba(221,242,250,.95), transparent 34%),
            linear-gradient(135deg, #F7FCFD 0%, #FFFFFF 58%);
        border: 1px solid var(--line);
        box-shadow: 0 18px 50px rgba(18,48,74,.07);
        margin-bottom: 1.8rem;
    }

    .hero-badge {
        display: inline-flex;
        padding: .45rem .72rem;
        border-radius: 999px;
        background: rgba(44,143,120,.10);
        color: var(--green-dark);
        font-weight: 800;
        font-size: .82rem;
        margin-bottom: 1rem;
    }

    .hero h1 {
        max-width: 820px;
        font-size: clamp(2.4rem, 5vw, 4.7rem);
        line-height: .98;
        margin: 0 0 1rem;
    }

    .hero p {
        max-width: 740px;
        color: var(--muted);
        font-size: 1.15rem;
        line-height: 1.7;
    }

    .module-card {
        min-height: 210px;
        padding: 1.3rem;
        border-radius: 20px;
        border: 1px solid var(--line);
        background: var(--white);
        margin-bottom: 1rem;
    }

    .module-icon {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: grid;
        place-items: center;
        background: var(--blue-soft);
        font-size: 1.35rem;
        margin-bottom: 1rem;
    }

    .module-card p,
    .muted {
        color: var(--muted);
    }

    .section-box {
        background: var(--soft);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 1.6rem;
        margin: 1rem 0;
    }

    .notice {
        border-left: 4px solid var(--green);
        background: #F4FBF8;
        padding: 1rem 1.1rem;
        border-radius: 12px;
        margin: 1rem 0;
    }

    .warning-box {
        border-left: 4px solid #D6A800;
        background: var(--warning);
        padding: 1rem 1.1rem;
        border-radius: 12px;
        margin: 1rem 0;
    }

    .footer {
        margin-top: 3rem;
        border-top: 1px solid var(--line);
        padding-top: 1.4rem;
        color: var(--muted);
        font-size: .85rem;
    }

    @media (max-width: 850px) {
        .topbar {
            align-items: flex-start;
            flex-direction: column;
        }

        .hero {
            padding: 2.1rem 1.3rem;
            border-radius: 22px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATOS DEMOSTRATIVOS
# =========================================================

@dataclass(frozen=True)
class VaccineCard:
    name: str
    disease: str
    stage: str
    summary: str
    status: str = "Borrador"


VACCINES: List[VaccineCard] = [
    VaccineCard(
        name="Ficha demostrativa 01",
        disease="Contenido sanitario pendiente de validación",
        stage="Infancia",
        summary="La estructura está preparada para incluir esquema, dosis, fuente y fecha de revisión.",
    ),
    VaccineCard(
        name="Ficha demostrativa 02",
        disease="Contenido sanitario pendiente de validación",
        stage="Adolescencia",
        summary="La publicación definitiva requerirá revisión humana y fuente oficial.",
    ),
    VaccineCard(
        name="Ficha demostrativa 03",
        disease="Contenido sanitario pendiente de validación",
        stage="Adultez",
        summary="La plataforma no determina vacunas faltantes ni reemplaza el carnet.",
    ),
]

CALENDAR_STAGES: Dict[str, str] = {
    "Embarazo": "Espacio preparado para información oficial validada durante el embarazo.",
    "Recién nacido": "Información organizada desde el nacimiento.",
    "Infancia": "Etapa infantil con navegación progresiva y fichas verificables.",
    "Edad escolar": "Información vinculada a la etapa escolar.",
    "Adolescencia": "Información clara para adolescentes y familias.",
    "Adultez": "Orientación general por etapa de vida y situaciones especiales.",
    "Personas mayores": "Acceso legible y accesible a información relevante.",
}

INFO_TOPICS = [
    "Seguridad de las vacunas",
    "Embarazo",
    "Vacunación infantil",
    "Adolescencia",
    "Personas mayores",
    "Enfermedades crónicas",
    "Viajes",
    "Esquemas atrasados",
    "Pérdida del carnet",
    "Mitos y desinformación",
]


# =========================================================
# COMPONENTES
# =========================================================

def render_header() -> None:
    st.markdown(
        f"""
        <div class="topbar">
            <div class="brand">VACUNACION <span>Plataforma Digital</span></div>
            <div class="status-chip">MVP funcional · Contenido en validación</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        f"""
        <div class="footer">
            <strong>{DEVELOPER}</strong><br>
            {MEDICAL_NOTICE}
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        placeholder="Ej.: vacuna contra la gripe, perdí el carnet, estoy embarazada...",
    )
    if query:
        st.info(
            f"Consulta recibida: “{query}”. El buscador definitivo se conectará únicamente "
            "a contenidos aprobados."
        )

    st.markdown("## Accesos principales")

    modules = [
        ("📅", "Calendario", "Recorré la vacunación por etapa de vida."),
        ("🧭", "Orientación", "Recibí orientación general basada en reglas."),
        ("💉", "Vacunas", "Consultá fichas claras, trazables y verificables."),
        ("📘", "Información", "Embarazo, viajes, carnet, mitos y más."),
        ("📍", "Dónde vacunarme", "Accedé a centros y datos territoriales."),
        ("🔔", "Novedades", "Campañas, operativos y alertas vigentes."),
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


def render_calendar() -> None:
    st.title("Calendario de vacunación")
    st.caption("Estructura interactiva por etapa de vida.")

    stage = st.segmented_control(
        "Etapa de vida",
        options=list(CALENDAR_STAGES.keys()),
        default="Embarazo",
        label_visibility="collapsed",
    )

    st.markdown(
        f"""
        <div class="section-box">
            <h2>{stage}</h2>
            <p class="muted">{CALENDAR_STAGES[stage]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="warning-box">
            <strong>BORRADOR — NO PUBLICAR.</strong><br>
            Esta versión prueba la arquitectura y la experiencia de usuario.
            Todavía no contiene un calendario sanitario oficial.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_orientation() -> None:
    st.title("¿Qué vacunas podrían corresponderme?")
    st.caption("Orientación general basada en reglas. No reemplaza la consulta profesional.")

    with st.form("orientation_form"):
        age = st.number_input("Edad", min_value=0, max_value=120, step=1)
        pregnancy = st.selectbox("¿Cursa un embarazo?", ["No corresponde", "No", "Sí"])
        chronic = st.selectbox("¿Tiene alguna enfermedad crónica?", ["No sé", "No", "Sí"])
        travel = st.selectbox("¿Tiene un viaje próximo?", ["No", "Sí"])
        card = st.selectbox("¿Tiene disponible su carnet?", ["Sí", "No", "No sé"])
        submitted = st.form_submit_button("Obtener orientación general")

    if submitted:
        st.markdown(
            f"""
            <div class="notice">
                <strong>Según la información ingresada</strong>, el sistema podría mostrar
                contenidos relevantes para una persona de {age} años.
                Verificá tu carnet o consultá en un vacunatorio.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if pregnancy == "Sí":
            st.info("Se priorizarán contenidos aprobados relacionados con embarazo.")
        if chronic == "Sí":
            st.info("Se priorizarán contenidos aprobados sobre condiciones crónicas.")
        if travel == "Sí":
            st.info("Se priorizarán contenidos aprobados relacionados con viajes.")
        if card != "Sí":
            st.info("Se mostrará información sobre cómo recuperar o verificar antecedentes.")


def render_vaccines() -> None:
    st.title("Biblioteca de vacunas")
    st.caption("Fichas estructuradas, revisables y preparadas para contenido oficial.")

    query = st.text_input("Buscar vacuna, enfermedad o etapa", key="vaccine_search")
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
            or q in item.disease.lower()
            or q in item.stage.lower()
            or q in item.summary.lower()
        ]

    if stage_filter != "Todas":
        results = [item for item in results if item.stage == stage_filter]

    if not results:
        st.warning("No se encontraron resultados.")

    for item in results:
        with st.expander(f"{item.name} · {item.stage}"):
            st.write(item.summary)
            st.caption(f"Estado editorial: {item.status}")
            st.info("Fuente oficial y fecha de revisión: pendientes de validación.")


def render_information() -> None:
    st.title("Información sobre vacunación")
    st.caption("Contenidos educativos organizados por situación y necesidad.")

    for topic in INFO_TOPICS:
        with st.expander(topic):
            st.write(
                "Sección preparada para contenido aprobado, referencias oficiales, "
                "fecha de revisión y preguntas frecuentes."
            )


def render_centers() -> None:
    st.title("Dónde vacunarme")
    st.caption("Módulo territorial inicial para San Francisco, Córdoba.")

    st.markdown(
        """
        <div class="warning-box">
            Los centros, horarios y coordenadas todavía no fueron verificados.
            No se publicarán ubicaciones hasta completar la validación institucional.
        </div>
        """,
        unsafe_allow_html=True,
    )

    centers = pd.DataFrame(
        [
            {
                "Centro": "Centro pendiente de verificación",
                "Localidad": "San Francisco",
                "Provincia": "Córdoba",
                "Estado": "Borrador",
            }
        ]
    )
    st.dataframe(centers, use_container_width=True, hide_index=True)


def render_news() -> None:
    st.title("Novedades y campañas")
    st.caption("Campañas, operativos y cambios temporales.")

    st.info("Todavía no hay novedades publicadas.")

    with st.expander("Flujo editorial previsto"):
        st.code("Borrador → Revisión → Aprobación → Publicación → Archivo")


def render_admin() -> None:
    st.title("Administración")
    st.caption("Prototipo interno de gestión editorial.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Contenidos en borrador", 3)
    col2.metric("Fuentes verificadas", 0)
    col3.metric("Centros verificados", 0)

    st.markdown(
        """
        <div class="section-box">
            <h3>Módulos previstos</h3>
            <p class="muted">
                Contenidos · Vacunatorios · Fuentes oficiales · Versionado ·
                Analítica anónima · Configuración · Seguridad
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# APLICACIÓN
# =========================================================

render_header()

sections = [
    "Inicio",
    "Calendario",
    "Orientación",
    "Vacunas",
    "Información",
    "Dónde vacunarme",
    "Novedades",
    "Administración",
]

selected = st.radio(
    "Navegación",
    sections,
    horizontal=True,
    label_visibility="collapsed",
)

if selected == "Inicio":
    render_home()
elif selected == "Calendario":
    render_calendar()
elif selected == "Orientación":
    render_orientation()
elif selected == "Vacunas":
    render_vaccines()
elif selected == "Información":
    render_information()
elif selected == "Dónde vacunarme":
    render_centers()
elif selected == "Novedades":
    render_news()
elif selected == "Administración":
    render_admin()

render_footer()
