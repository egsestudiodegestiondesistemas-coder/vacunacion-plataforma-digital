import streamlit as st
from src.components.page_shell import start_page, end_page
start_page("Calendario de vacunación","Calendario","Recorré el calendario oficial por etapa de vida.")
stage=st.selectbox("Seleccioná una etapa",["Embarazo","Recién nacido","Primeros meses","Infancia","Edad escolar","Adolescencia","Adultez","Personas mayores","Situaciones especiales"])
st.markdown(f'<div class="notice">Contenido oficial en preparación para: <strong>{stage}</strong>.</div>', unsafe_allow_html=True)
end_page()
