from __future__ import annotations

import streamlit as st

from utils import apply_chart_style, render_section_note


def render(ctx: dict) -> None:
    queue_df = ctx["queue_df"]
    history_df = ctx["history_df"]

    st.subheader("Review Queue And History")
    render_section_note(
        "This queue uses miss pressure, recency, current streaks, and your onboarding confidence ratings to decide what should be reviewed now versus what can wait."
    )
    if not queue_df.empty:
        st.markdown("### Spaced Repetition Queue")
        st.dataframe(queue_df, use_container_width=True, hide_index=True)
    else:
        st.info("Take a few quizzes to build the review queue.")

    if not history_df.empty:
        import plotly.express as px

        st.markdown("### Topic Streak History")
        history_fig = px.scatter(
            history_df,
            x="submitted_at",
            y="topic",
            color="result",
            symbol="result",
            hover_data=["domain", "streak_after_attempt"],
            title="Per-Topic History",
        )
        st.plotly_chart(apply_chart_style(history_fig, height=420), use_container_width=True)
        st.dataframe(
            history_df[["submitted_at", "domain", "topic", "result", "streak_after_attempt"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Topic history appears once you save scored attempts.")
