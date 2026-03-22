from __future__ import annotations

import streamlit as st

from exams import EXAM_DOMAINS
from question_engine import generate_quiz
from utils import render_section_note
from pages._shared import _build_quiz_session, _persist_session, _render_quiz_form


def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]
    selected_count = ctx["selected_count"]
    timed_mode = ctx["timed_mode"]
    minutes = ctx["minutes"]

    st.subheader("Practice Quiz Generator")
    render_section_note(
        "Use shorter focused sets when you need reps. The recommendation engine now lowers priority for topics that are already on a correct-answer streak."
    )
    practice_domains = st.multiselect(
        "Select exam domains",
        EXAM_DOMAINS[selected_exam],
        default=EXAM_DOMAINS[selected_exam],
        key="practice_domains",
    )
    generate_practice = st.button("Generate Practice Quiz", type="primary", use_container_width=True)
    if generate_practice:
        if not practice_domains:
            st.warning("Select at least one domain before generating a practice quiz.")
        else:
            st.session_state["practice_result"] = None
            st.session_state["practice_quiz"] = _build_quiz_session(
                selected_exam,
                generate_quiz(selected_exam, practice_domains, selected_count, "practice"),
                timed_mode,
                int(minutes) if timed_mode else None,
                "Practice Quiz",
                "practice",
            )
            _persist_session("practice_quiz")
    _render_quiz_form("practice_quiz", "practice_result", "Practice Quiz", "practice", False)
