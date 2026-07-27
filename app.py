import streamlit as st
from src.components.layout import render_header, render_footer
from src.utils.page import configure_page
from src.utils.styles import inject_global_styles

configure_page("VACUNACION Plataforma Digital")
inject_global_styles()
render_header("Inicio")

st.markdown(
    '''
    <section class="hero">
        <div class="hero-badge">Información pública clara y confiable</div>
        <h1>Todo sobre vacunación, en un solo lugar.</h1>
        <p class="hero-copy">Consultá el calendario, recibí orientación general, conocé cada vacuna y encontrá dónde vacunarte.</p>
        <div class="hero-actions">
            <a class="btn btn-primary" href="/Orientacion">Consultar orientación</a>
            <a class="btn btn-secondary" href="/Calendario">Ver calendario</a>
            <a class="btn btn-ghost" href="/Donde_vacunarme">Encontrar vacunatorio</a>
        </div>
    </section>
    ''',
    unsafe_allow_html=True,
)

st.text_input("Buscar", placeholder="Ej.: vacuna contra la gripe, perdí el carnet, estoy embarazada...")

st.markdown("## Accesos principales")
cards = [
    ("Calendario de vacunación","Recorré el calendario por etapa de vida.","📅","Calendario"),
    ("¿Qué vacunas podrían corresponderme?","Orientación general basada en información oficial.","🧭","Orientacion"),
    ("Vacunas","Consultá fichas claras y completas.","💉","Vacunas"),
    ("Información","Embarazo, viajes, mitos, carnet perdido y más.","📘","Informacion"),
    ("Dónde vacunarme","Encontrá centros, horarios y rutas.","📍","Donde_vacunarme"),
    ("Novedades","Campañas, operativos y alertas vigentes.","🔔","Novedades"),
]
cols = st.columns(3, gap="large")
for i,(title,desc,icon,slug) in enumerate(cards):
    with cols[i%3]:
        st.markdown(f'<article class="feature-card"><div class="feature-icon">{icon}</div><h3>{title}</h3><p>{desc}</p><a href="/{slug}">Abrir sección →</a></article>', unsafe_allow_html=True)

render_footer()
