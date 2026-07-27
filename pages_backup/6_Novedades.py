import streamlit as st
from src.components.page_shell import start_page, end_page
start_page("Novedades y campañas","Novedades","Campañas, operativos, alertas y cambios temporales.")
st.info("Todavía no hay novedades publicadas.")
end_page()
