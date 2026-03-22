from __future__ import annotations

import pandas as pd
import streamlit as st

from tracker import recommend_study_next, weakest_topics
from utils import render_section_note


def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]
    exam_results = ctx["exam_results"]
    profile = ctx["profile"]

    st.subheader("Weak Topic Radar")
    render_section_note(
        "Recent misses now carry more weight than older misses, but repeated correct answers reduce urgency so you do not overfocus on already-recovering topics."
    )
    weak_df = pd.DataFrame(weakest_topics(selected_exam, exam_results, limit=12))
    if not weak_df.empty:
        st.dataframe(
            weak_df[["domain", "topic", "weighted_accuracy", "miss_pressure", "correct_streak", "priority_score"]],
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("### What To Study Next")
        for line in recommend_study_next(selected_exam, exam_results, profile):
            st.write(f"- {line}")
    else:
        st.info("No weak-topic model yet. Your misses will start shaping priority as soon as attempts are saved.")
