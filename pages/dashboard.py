from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from storage import (
    LEVEL_THRESHOLDS,
    build_quiz_history_frame,
    export_dataframe,
    export_markdown,
    get_active_misconceptions,
    get_badges,
    get_boss_battle_history,
    get_boss_battle_stats,
    get_debate_stats,
    get_level_info,
    get_streak,
    load_user_profile,
    resolve_misconception,
)
from tracker import (
    build_markdown_study_summary,
    improved_topics,
    performance_over_time,
    readiness_history,
    strongest_topics,
    weakest_topics,
)
from utils import (
    apply_chart_style,
    render_insight_card,
    render_metric_card,
    render_section_note,
)
from pages._shared import _storage_caption


def _render_xp_panel() -> None:
    level = get_level_info()
    streak = get_streak()
    badges = get_badges()
    recent_badges = sorted(badges, key=lambda b: b["earned_at"], reverse=True)[:3]

    st.markdown("### Player Progress")
    left, mid, right = st.columns([2.2, 0.9, 1.9])

    with left:
        next_title = level["next_level_title"]
        bar_label = (
            f"{level['xp_to_next']:,} XP to {next_title}"
            if level["xp_to_next"] > 0
            else "Max level reached!"
        )
        st.markdown(
            f"**Level {level['level_index'] + 1} — {level['level_title']}** &nbsp;·&nbsp; "
            f"{level['current_xp']:,} XP total",
            unsafe_allow_html=True,
        )
        st.progress(level["progress_pct"] / 100, text=bar_label)

    with mid:
        streak_count = streak.get("current_streak", 0)
        label = f"{streak_count} day{'s' if streak_count != 1 else ''}"
        st.metric("🔥 Streak", label)

    with right:
        if recent_badges:
            st.caption("Recent badges")
            for b in recent_badges:
                st.markdown(f"🏅 **{b['badge_name']}** — {b['description']}")
        if badges:
            with st.expander(f"View all badges ({len(badges)})"):
                for b in sorted(badges, key=lambda x: x["earned_at"], reverse=True):
                    st.markdown(f"🏅 **{b['badge_name']}** — {b['description']}")
                    st.caption(f"Earned {b['earned_at'][:10]}")
        else:
            st.caption("No badges yet — complete a quiz to earn your first!")

    st.divider()


def _export_section(selected_exam: str, all_results: list[dict], exam_results: list[dict]) -> None:
    st.markdown("### Power BI Export Prep")
    render_section_note(
        "Use these exports to feed Power BI locally. When local file persistence is available, files are written to data/exports so refreshes can point at a stable folder."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Export Quiz History", use_container_width=True):
            frame = build_quiz_history_frame(all_results)
            path = export_dataframe(frame, "quiz_history.csv")
            if path:
                st.success(f"Saved {path.name} to data/exports.")
            else:
                st.warning("Quiz history export is unavailable in cloud/demo mode because local file writes are disabled.")
    with c2:
        if st.button(f"Export {selected_exam} Weak Topics", use_container_width=True):
            frame = pd.DataFrame(
                weakest_topics(selected_exam, exam_results, limit=25),
                columns=[
                    "domain",
                    "topic",
                    "attempts",
                    "weighted_accuracy",
                    "correct_streak",
                    "miss_pressure",
                    "priority_score",
                ],
            )
            path = export_dataframe(frame, f"weak_topics_{selected_exam.lower().replace('+', 'plus').replace(' ', '_')}.csv")
            if path:
                st.success(f"Saved {path.name} to data/exports.")
            else:
                st.warning("Weak-topic export is unavailable in cloud/demo mode because local file writes are disabled.")
    with c3:
        if st.button(f"Export {selected_exam} Readiness History", use_container_width=True):
            frame = readiness_history(selected_exam, exam_results)
            path = export_dataframe(
                frame,
                f"readiness_history_{selected_exam.lower().replace('+', 'plus').replace(' ', '_')}.csv",
            )
            if path:
                st.success(f"Saved {path.name} to data/exports.")
            else:
                st.warning("Readiness-history export is unavailable in cloud/demo mode because local file writes are disabled.")

    st.markdown("### Markdown Study Summary")
    render_section_note(
        "Create a polished markdown progress summary for GitHub, a portfolio repo, or a LinkedIn post draft."
    )
    if st.button("Export Markdown Study Summary", use_container_width=True):
        content = build_markdown_study_summary(all_results, load_user_profile())
        path = export_markdown(content, "study_summary.md")
        if path:
            st.success(f"Saved {path.name} to data/exports.")
        else:
            st.warning("Markdown export is unavailable in cloud/demo mode because local file writes are disabled.")


def _render_debate_stats() -> None:
    stats = get_debate_stats()
    if stats["total"] == 0:
        return
    st.markdown("### Debate Mode Stats")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Debates Completed", stats["total"])
    c2.metric("Average Score", f"{stats['avg_score']}/10")
    c3.metric("High Scores (8+)", stats["high_scores"])
    c4.metric("Strongest Domain", stats["strongest_domain"])
    st.divider()


def _render_misconceptions() -> None:
    misconceptions = get_active_misconceptions()
    if not misconceptions:
        return

    st.markdown("### Detected Misconceptions")
    render_section_note(
        "These patterns were detected from repeated wrong-answer selections across your quiz history. "
        "Click Resolved when you feel confident you understand the concept."
    )

    for m in misconceptions[:3]:
        with st.expander(
            f"**{m.get('domain')}** — {m.get('topic')} ({m.get('exam')})",
            expanded=True,
        ):
            st.markdown(f"**Repeated wrong answer:** {m.get('wrong_pattern')}")
            st.info(m.get("correction", ""))
            if st.button("Mark as Resolved", key=f"resolve_mc_{m.get('id')}"):
                resolve_misconception(m["id"])
                st.success("Marked as resolved!")
                st.rerun()
    st.divider()


def _render_boss_battle_history() -> None:
    stats = get_boss_battle_stats()
    history = get_boss_battle_history(limit=5)
    if not history:
        return

    st.markdown("### Boss Battle History")
    col1, col2, col3 = st.columns(3)
    col1.metric("Battles Completed", stats["total"])
    col2.metric("Best Score", f"{stats['best_score']}/10")
    col3.metric("Best Recommendation", stats["best_rec"] or "—")

    rows = []
    for b in history:
        rows.append({
            "Exam": b.get("exam", ""),
            "Score": f"{b.get('score', 0)}/{b.get('total_questions', 10)}",
            "Recommendation": b.get("hiring_rec") or "—",
            "Date": (b.get("completed_at") or "")[:10],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.divider()


def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]
    exam_results = ctx["exam_results"]
    all_results = ctx["all_results"]
    current_readiness = ctx["current_readiness"]
    current_latest_score = ctx["current_latest_score"]
    prediction = ctx["prediction"]
    recommended = ctx["recommended"]
    domain_conf_df = ctx["domain_conf_df"]
    queue_df = ctx["queue_df"]

    _render_xp_panel()
    weakest = weakest_topics(selected_exam, exam_results, limit=5)
    strongest = strongest_topics(selected_exam, exam_results, limit=5)
    metrics = st.columns(4)
    with metrics[0]:
        render_metric_card("Readiness Score", f"{current_readiness:.1f}", "Personalized by profile and history")
    with metrics[1]:
        render_metric_card("Total Attempts", str(len(exam_results)), _storage_caption())
    with metrics[2]:
        render_metric_card("Latest Score", f"{current_latest_score:.1f}%", "Most recent attempt")
    with metrics[3]:
        render_metric_card(
            "Predicted Range",
            f"{prediction['range_low']:.0f}-{prediction['range_high']:.0f}%",
            "Local score estimate",
        )

    top_left, top_right = st.columns([1.1, 1])
    with top_left:
        render_insight_card(
            "Recommended Next Topic",
            f"{recommended['topic']} in {recommended['domain']}. {recommended['reason']}",
            pills=[f"Confidence gap: {recommended['confidence_gap']:.0f} pts"],
        )
    with top_right:
        render_insight_card(
            "Prediction Confidence",
            prediction["confidence_note"],
            pills=[
                f"{prediction['history_count']} saved attempts",
                f"{prediction['question_volume']} questions logged",
            ],
        )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Weakest Topics")
        if weakest:
            weak_df = pd.DataFrame(weakest)[["domain", "topic", "weighted_accuracy", "miss_pressure", "correct_streak"]]
            st.dataframe(weak_df, use_container_width=True, hide_index=True)
        else:
            st.info("Take a quiz to surface weak topics.")
    with col2:
        st.markdown("### Strongest Topics")
        if strongest:
            strong_df = pd.DataFrame(strongest)[["domain", "topic", "weighted_accuracy", "correct_streak", "attempts"]]
            st.dataframe(strong_df, use_container_width=True, hide_index=True)
        else:
            st.info("Strong topics appear after a few saved attempts.")

    perf_df = performance_over_time(selected_exam, exam_results)
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("### Performance Trend")
        if not perf_df.empty:
            perf_fig = px.line(
                perf_df,
                x="submitted_at",
                y=["score_pct", "rolling_score"],
                markers=True,
                title=f"{selected_exam} Score Trend",
            )
            perf_fig.update_traces(line_width=3)
            st.plotly_chart(apply_chart_style(perf_fig, height=370), use_container_width=True)
        else:
            st.info("No attempts logged yet.")
    with chart_right:
        st.markdown("### Confidence By Domain")
        if not domain_conf_df.empty:
            conf_fig = px.bar(
                domain_conf_df.sort_values("confidence_pct"),
                x="confidence_pct",
                y="domain",
                orientation="h",
                color="confidence_pct",
                color_continuous_scale=["#f6c453", "#0f766e"],
                title="Weighted Domain Confidence",
            )
            st.plotly_chart(apply_chart_style(conf_fig, height=370), use_container_width=True)
        else:
            st.info("Domain confidence appears after saved attempts.")

    if not queue_df.empty:
        st.markdown("### Spaced Repetition Queue")
        st.dataframe(queue_df.head(5), use_container_width=True, hide_index=True)

    improved = improved_topics(selected_exam, exam_results, limit=5)
    if improved:
        st.markdown("### Weak Topics Improved")
        st.dataframe(pd.DataFrame(improved), use_container_width=True, hide_index=True)

    if not domain_conf_df.empty:
        st.dataframe(
            domain_conf_df[["domain", "confidence_pct", "recent_avg", "attempts", "signal"]],
            use_container_width=True,
            hide_index=True,
        )

    _render_debate_stats()
    _render_misconceptions()
    _render_boss_battle_history()
    _export_section(selected_exam, all_results, exam_results)
