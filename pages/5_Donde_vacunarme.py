import streamlit as st
from src.components.page_shell import start_page, end_page
start_page("Dónde vacunarme","Dónde vacunarme","Mapa inteligente de vacunatorios de San Francisco, Córdoba.")
st.markdown('<div class="notice">El mapa incorporará geolocalización, filtros, rutas, horarios y fecha de verificación.</div>', unsafe_allow_html=True)
st.map()
end_page()
