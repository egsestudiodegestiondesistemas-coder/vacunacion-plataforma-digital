import streamlit as st
from src.components.layout import render_header, render_footer
from src.utils.page import configure_page
from src.utils.styles import inject_global_styles

def start_page(title: str, active: str, description: str) -> None:
    configure_page(f"{title} | VACUNACION Plataforma Digital")
    inject_global_styles()
    render_header(active)
    st.markdown(f'<section class="page-intro"><h1>{title}</h1><p>{description}</p></section>', unsafe_allow_html=True)

def end_page() -> None:
    render_footer()
