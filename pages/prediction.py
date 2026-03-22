from __future__ import annotations

import streamlit as st

from utils import apply_chart_style, render_insight_card, render_metric_card, render_section_note


def render(ctx: dict) -> None:
    prediction = ctx["prediction"]
    domain_conf_df = ctx["domain_conf_df"]

    st.subheader("Predicted Score")
    render_section_note(
        "This local estimate blends recent quiz history, weighted domain confidence, accuracy, total question volume, and your saved study profile."
    )
    top = st.columns(3)
    with top[0]:
        render_metric_card("Predicted Score", f"{prediction['predicted_score']:.1f}%")
    with top[1]:
        render_metric_card("Predicted Range", f"{prediction['range_low']:.0f}-{prediction['range_high']:.0f}%")
    with top[2]:
        render_metric_card("Questions Used", str(prediction["question_volume"]))
    render_insight_card("Confidence Note", prediction["confidence_note"])
    if not domain_conf_df.empty:
        import plotly.express as px

        pred_fig = px.scatter(
            domain_conf_df,
            x="attempts",
            y="confidence_pct",
            size="confidence_pct",
            color="signal",
            hover_name="domain",
            title="Domain Confidence Signals",
        )
        st.plotly_chart(apply_chart_style(pred_fig, height=380), use_container_width=True)
    st.markdown("### How To Improve The Prediction")
    st.write("- Save more medium-length practice quizzes across multiple domains.")
    st.write("- Add at least one timed simulator attempt if you have only been using untimed mode.")
    st.write("- Re-test domains with low confidence so the range tightens around current performance.")
