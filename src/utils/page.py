import streamlit as st

def configure_page(title: str, icon: str = "💉") -> None:
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
