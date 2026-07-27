import streamlit as st
from src.components.page_shell import start_page, end_page
start_page("Vacunas","Vacunas","Biblioteca moderna de vacunas, enfermedades y esquemas.")
st.text_input("Buscar una vacuna o enfermedad",placeholder="Ej.: gripe, VPH, tétanos")
st.info("Las fichas oficiales se cargarán en la siguiente fase.")
end_page()
