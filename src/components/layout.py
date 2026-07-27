import streamlit as st

NAV_ITEMS = [
    ("Inicio", "/"),
    ("Calendario", "/Calendario"),
    ("Orientación", "/Orientacion"),
    ("Vacunas", "/Vacunas"),
    ("Información", "/Informacion"),
    ("Dónde vacunarme", "/Donde_vacunarme"),
    ("Novedades", "/Novedades"),
]

def render_header(active: str) -> None:
    links = []
    for label, href in NAV_ITEMS:
        css = "nav-link active" if label == active else "nav-link"
        links.append(f'<a class="{css}" href="{href}">{label}</a>')
    st.markdown(
        f'<div class="topbar"><a class="brand" href="/">VACUNACION <span>Plataforma Digital</span></a><nav class="nav-links">{"".join(links)}</nav></div>',
        unsafe_allow_html=True,
    )

def render_footer() -> None:
    st.markdown(
        '<footer class="site-footer"><strong>EGS | Estudio de Gestión de Sistemas</strong><span>Información general. No reemplaza la consulta profesional.</span></footer>',
        unsafe_allow_html=True,
    )
