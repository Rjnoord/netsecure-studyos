from __future__ import annotations

import streamlit as st

from exams import get_cheat_sheet, list_topics_for_exam
from utils import render_section_note, render_topic_card


def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]

    st.subheader("Cheat Sheets")
    render_section_note(
        "Cheat sheets now surface key terms, memory tips, why the topic matters, and common mistakes to avoid before your next attempt."
    )
    topic_options = list_topics_for_exam(selected_exam)
    chosen_topic = st.selectbox("Select topic", topic_options)
    cheat_sheet = get_cheat_sheet(selected_exam, chosen_topic)
    left, right = st.columns([1.2, 1])
    with left:
        render_topic_card(
            chosen_topic,
            [f"Why it matters: {cheat_sheet['why_it_matters']}"] + cheat_sheet["summary"],
            pills=cheat_sheet["key_terms"][:5],
        )
    with right:
        render_topic_card("Memory Tips", cheat_sheet["memory_tips"] or ["No memory tips yet."])
    st.markdown("### Key Terms")
    st.write(", ".join(cheat_sheet["key_terms"]) if cheat_sheet["key_terms"] else "No key terms yet.")
    st.markdown("### Common Mistakes / Watch-Outs")
    if cheat_sheet["watch_outs"]:
        for warning in cheat_sheet["watch_outs"]:
            st.write(f"- {warning}")
    else:
        st.info("Watch-outs appear as more cheat-sheet detail is added.")
