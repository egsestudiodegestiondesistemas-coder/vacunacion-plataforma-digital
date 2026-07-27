import streamlit as st
from src.components.page_shell import start_page, end_page
start_page("¿Qué vacunas podrían corresponderme?","Orientación","Orientación general basada en reglas sanitarias.")
with st.form("orientation"):
    age=st.number_input("Edad",0,120,0)
    pregnancy=st.selectbox("¿Cursa un embarazo?",["No corresponde","No","Sí"])
    chronic=st.selectbox("¿Tiene alguna enfermedad crónica?",["No sé","No","Sí"])
    travel=st.selectbox("¿Tiene un viaje próximo?",["No","Sí"])
    has_card=st.selectbox("¿Tiene disponible su carnet?",["Sí","No","No sé"])
    ok=st.form_submit_button("Obtener orientación general")
if ok:
    st.markdown('<div class="notice"><strong>Según la información ingresada</strong>, estas orientaciones podrían aplicar. Verificá tu carnet o consultá en un vacunatorio.</div>', unsafe_allow_html=True)
end_page()
