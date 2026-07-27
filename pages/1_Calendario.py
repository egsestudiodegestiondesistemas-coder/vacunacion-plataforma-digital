import streamlit as st
from src.components.calendar import render_stage_panel, render_stage_selector
from src.components.page_shell import end_page, start_page
from src.utils.data_loader import load_json

start_page(
    title="Calendario de vacunación",
    active="Calendario",
    description="Explorá la estructura del calendario por etapa de vida. Los contenidos sanitarios se publicarán únicamente después de revisión.",
)

data = load_json("src/data/calendar_demo.json")
st.warning(data["meta"]["status"])
st.caption(data["meta"]["purpose"])

stages = data["stages"]
selected_label = render_stage_selector(stages)
selected_stage = next(stage for stage in stages if stage["label"] == selected_label)
render_stage_panel(selected_stage)

st.markdown('<div class="notice"><strong>Importante:</strong> esta versión prueba la arquitectura y la experiencia de usuario. Todavía no contiene un calendario sanitario oficial.</div>', unsafe_allow_html=True)
end_page()
