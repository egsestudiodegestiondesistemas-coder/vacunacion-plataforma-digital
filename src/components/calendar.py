import html
import streamlit as st

def render_stage_selector(stages: list[dict]) -> str:
    labels = [stage["label"] for stage in stages]
    return st.segmented_control(
        "Etapa de vida",
        options=labels,
        default=labels[0],
        label_visibility="collapsed",
        key="calendar_stage_selector",
    )

def render_stage_panel(stage: dict) -> None:
    icon = html.escape(stage.get("icon", ""))
    label = html.escape(stage.get("label", ""))
    description = html.escape(stage.get("description", ""))
    st.markdown(
        f'<section class="calendar-stage"><div class="calendar-stage-icon">{icon}</div><div><span class="calendar-kicker">Etapa seleccionada</span><h2>{label}</h2><p>{description}</p></div></section>',
        unsafe_allow_html=True,
    )
    for item in stage.get("items", []):
        title = html.escape(item.get("title", ""))
        summary = html.escape(item.get("summary", ""))
        st.markdown(
            f'<article class="calendar-item"><div class="calendar-dot"></div><div><span class="draft-badge">BORRADOR</span><h3>{title}</h3><p>{summary}</p></div></article>',
            unsafe_allow_html=True,
        )
