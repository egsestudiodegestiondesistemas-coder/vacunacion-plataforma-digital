import streamlit as st
from src.components.page_shell import start_page, end_page
start_page("Información sobre vacunación","Información","Contenidos claros sobre embarazo, viajes, esquemas atrasados y mitos.")
for t in ["Seguridad de las vacunas","Embarazo","Vacunación infantil","Adolescencia","Personas mayores","Enfermedades crónicas","Viajes","Esquemas atrasados","Pérdida del carnet","Mitos y desinformación"]:
    with st.expander(t): st.write("Contenido oficial en preparación.")
end_page()
