from __future__ import annotations

import streamlit as st

from tracker import build_study_plan
from utils import render_insight_card, render_metric_card, render_section_note, render_topic_card


def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]
    exam_results = ctx["exam_results"]
    profile = ctx["profile"]
    study_hours = ctx["study_hours"]

    st.subheader("Study Plan Builder")
    render_section_note(
        "This plan now prioritizes the weakest areas first, estimates time per topic, and explains why each topic matters."
    )
    hours_available = st.slider("Hours available this week", min_value=2, max_value=25, value=study_hours)
    plan = build_study_plan(selected_exam, hours_available, exam_results, profile)
    topic_cols = st.columns(min(4, max(1, len(plan["topics"]))))
    for index, topic in enumerate(plan["topics"][:4]):
        with topic_cols[index]:
            render_metric_card(
                f"Priority {topic['priority']}",
                topic["topic"],
                f"{topic['estimated_minutes']} min planned",
            )
    st.markdown("### Plan Output")
    for topic in plan["topics"]:
        render_topic_card(
            f"Priority {topic['priority']} • {topic['topic']}",
            [
                f"Domain: {topic['domain']}",
                f"Estimated time: {topic['estimated_minutes']} minutes",
                f"Why it matters: {topic['why_it_matters']}",
                f"Suggested session: {topic['focus']}",
            ],
            pills=[f"{topic['estimated_minutes']} min", topic["domain"]],
        )
    render_insight_card(
        "Recovery Block",
        f"Reserve {plan['recovery_block_minutes']} minutes for miss review and one short timed set.",
        pills=["Protect the final review block"],
    )
    st.write(plan["closing_step"])
