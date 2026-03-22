from __future__ import annotations

import streamlit as st

from exams import EXAM_DOMAINS
from question_engine import generate_quiz
from utils import render_insight_card, render_section_note
from pages._shared import _build_quiz_session, _persist_session, _render_quiz_form


def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]
    timed_mode = ctx["timed_mode"]
    minutes = ctx["minutes"]

    st.subheader("Exam Simulator")
    render_section_note(
        "Simulator mode keeps coverage broad. The 100-question fatigue simulation includes a dedicated endurance summary after scoring."
    )
    sim_count = st.selectbox(
        "Simulator length",
        [90, 100],
        index=0,
        format_func=lambda value: f"{value} Questions{' • Fatigue Simulation' if value == 100 else ''}",
    )
    if sim_count == 100:
        render_insight_card(
            "Fatigue Mode",
            "This run is meant to expose late-session decision drift. The full session can now be resumed from saved local progress.",
            pills=["Progress tracking", "Resume supported", "Recovery plan"],
            warning=True,
        )
    if st.button("Launch Exam Simulator", use_container_width=True):
        st.session_state["sim_result"] = None
        st.session_state["sim_quiz"] = _build_quiz_session(
            selected_exam,
            generate_quiz(selected_exam, EXAM_DOMAINS[selected_exam], sim_count, "exam"),
            timed_mode,
            int(minutes) if timed_mode else None,
            "Exam Simulator",
            "exam_simulator",
        )
        _persist_session("sim_quiz")
    _render_quiz_form("sim_quiz", "sim_result", "Exam Simulator", "exam_simulator", True)
