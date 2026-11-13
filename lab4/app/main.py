import json
from pathlib import Path

import streamlit as st

from audience import render_audience
from brief import render_brief
from creatives import render_creatives
from hooks import render_hooks
from layout import render_header, render_footer


st.set_page_config(
    page_title="AI Marketing Strategist",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

css_path = Path(__file__).resolve().with_name("style.css")

if css_path.exists():
    st.html(css_path)
else:
    st.warning("Не знайдено файл style.css")

stage = st.session_state.setdefault("stage", "brief")

render_header(stage)

if stage == "brief":
    render_brief()

elif stage == "audience":
    render_audience()

    brief = st.session_state.get("brief")
    segments = st.session_state.get("audience_segments")

    if brief and segments:
        brief_signature = json.dumps(
            brief,
            ensure_ascii=False,
            sort_keys=True,
        )

        if st.session_state.get("audience_brief_signature") == brief_signature:
            st.divider()
            if st.button(
                "Перейти до рекламних хуків →",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["stage"] = "hooks"
                st.rerun()
        else:
            st.warning(
                "Бриф змінився після аналізу. "
                "Оновіть результати ЦА перед переходом до хуків."
            )

elif stage == "hooks":
    render_hooks()

elif stage == "creatives":
    render_creatives()

render_footer(stage)
