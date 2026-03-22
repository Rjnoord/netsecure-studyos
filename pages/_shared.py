from __future__ import annotations

from datetime import datetime
from html import escape
from uuid import uuid4

import pandas as pd
import plotly.express as px
import streamlit as st

from exams import EXAM_DOMAINS
from question_engine import award_quiz_xp, evaluate_submission, get_ai_tutor_explanation
from storage import (
    add_xp,
    delete_active_session,
    is_file_persistence_enabled,
    load_results,
    save_active_session,
    save_mobile_sync,
    save_quiz_result,
    save_user_profile,
    load_user_profile,
    default_profile,
)
from tracker import (
    build_mobile_sync_payload,
    calculate_readiness,
    detect_misconceptions,
    fatigue_breakdown,
)
from utils import (
    apply_chart_style,
    countdown_html,
    format_timestamp,
    render_insight_card,
    render_metric_card,
    render_section_note,
    render_topic_card,
)


def _storage_caption() -> str:
    return "Saved locally" if is_file_persistence_enabled() else "Saved in memory for this session"


def _sync_mobile_data(profile: dict, all_results: list[dict]) -> None:
    save_mobile_sync(build_mobile_sync_payload(profile, all_results))


def _refresh_profile() -> dict:
    profile = load_user_profile()
    all_results = load_results()
    profile["updated_at"] = datetime.now().isoformat()
    profile["exam_readiness"] = {
        exam: round(calculate_readiness(exam, all_results, profile), 1) for exam in EXAM_DOMAINS
    }
    save_user_profile(profile)
    _sync_mobile_data(profile, all_results)
    return profile


def _save_onboarding(profile: dict, target_exam: str, target_date, weekly_hours: int, domain_ratings: dict[str, int]) -> dict:
    profile["onboarding_complete"] = True
    profile["target_exam"] = target_exam
    profile["target_date"] = target_date.isoformat()
    profile["weekly_study_hours"] = int(weekly_hours)
    profile.setdefault("domain_self_ratings", default_profile()["domain_self_ratings"])
    profile["domain_self_ratings"][target_exam] = domain_ratings
    save_user_profile(profile)
    return _refresh_profile()


def _build_quiz_session(exam: str, questions: list[dict], timed_mode: bool, minutes: int | None, label: str, save_mode: str) -> dict:
    started_at = datetime.now().replace(microsecond=0)
    ends_at = None
    if timed_mode and minutes:
        ends_at = (started_at + pd.Timedelta(minutes=int(minutes))).isoformat()
    return {
        "session_id": uuid4().hex[:10],
        "label": label,
        "mode": save_mode,
        "exam": exam,
        "questions": questions,
        "started_at": started_at.isoformat(),
        "timed_mode": timed_mode,
        "minutes": int(minutes) if timed_mode and minutes else None,
        "ends_at": ends_at,
        "answers": {},
        "last_touched_at": started_at.isoformat(),
    }


def _persist_session(quiz_key: str) -> None:
    payload = st.session_state.get(quiz_key)
    if not payload:
        return
    payload["last_touched_at"] = datetime.now().isoformat()
    save_active_session(payload)


def _clear_session(quiz_key: str) -> None:
    payload = st.session_state.get(quiz_key)
    if payload:
        delete_active_session(payload["session_id"])
    st.session_state[quiz_key] = None


def _result_metrics(result: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Score", f"{result['score_pct']:.1f}%")
    with c2:
        render_metric_card("Correct", f"{result['correct_count']}/{result['question_count']}")
    with c3:
        render_metric_card("Duration", f"{max(1, round(result['elapsed_seconds'] / 60))} min")
    with c4:
        render_metric_card("Completed", format_timestamp(result["submitted_at"]))


def _render_result_review(result: dict, show_exam_breakdown: bool) -> None:
    _result_metrics(result)

    if result.get("domain_breakdown"):
        df = pd.DataFrame(result["domain_breakdown"])
        if show_exam_breakdown:
            col1, col2 = st.columns([1.4, 1])
            with col1:
                fig = px.bar(
                    df,
                    x="domain",
                    y="accuracy_pct",
                    color="accuracy_pct",
                    color_continuous_scale=["#f6c453", "#0f766e"],
                    title="Domain-By-Domain Breakdown",
                )
                st.plotly_chart(apply_chart_style(fig, height=380), use_container_width=True)
            with col2:
                st.markdown("### Final Summary")
                for row in df.sort_values("accuracy_pct").to_dict(orient="records"):
                    status = "Strong" if row["accuracy_pct"] >= 80 else "Recover"
                    render_topic_card(
                        row["domain"],
                        [
                            f"Accuracy: {row['accuracy_pct']:.1f}%",
                            f"Correct: {row['correct']}/{row['total']}",
                        ],
                        pills=[status],
                    )
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    fatigue = fatigue_breakdown(result)
    if fatigue:
        st.markdown("### Fatigue Simulation Review")
        render_section_note(
            "This breakdown separates the long exam into blocks so you can see where concentration dropped and what to recover first."
        )
        left, right = st.columns([1.2, 1])
        with left:
            fatigue_df = pd.DataFrame(fatigue["blocks"])
            fig = px.line(
                fatigue_df,
                x="segment",
                y="accuracy_pct",
                markers=True,
                title="Accuracy Across Exam Blocks",
            )
            fig.update_traces(line_color="#b45309", marker_color="#0f766e", marker_size=10)
            st.plotly_chart(apply_chart_style(fig, height=320), use_container_width=True)
        with right:
            st.markdown("### Top Missed Topics")
            missed_df = pd.DataFrame(fatigue["top_missed_topics"])
            if not missed_df.empty:
                st.dataframe(missed_df, use_container_width=True, hide_index=True)
            else:
                st.info("No repeated misses surfaced in this fatigue simulation.")
        st.markdown("### Suggested Recovery Plan")
        for step in fatigue["recovery_plan"]:
            st.write(f"- {step}")

    st.markdown("### Review")
    for index, item in enumerate(result["questions"], start=1):
        outcome = "Correct" if item["is_correct"] else "Missed"
        with st.expander(f"Q{index} • {outcome} • {item['domain']}"):
            st.write(item["stem"])
            st.write(f"Your answer: {item['selected_answer'] or 'No answer selected'}")
            st.write(f"Correct answer: {item['correct_answer']}")
            st.write(item["explanation"])

            if not item["is_correct"]:
                tutor_cache_key = f"tutor_{item['id']}"
                tutor_xp_key = f"tutor_xp_{item['id']}"
                if tutor_cache_key in st.session_state:
                    explanation = st.session_state[tutor_cache_key]
                    if explanation is None:
                        st.warning("AI Tutor is temporarily unavailable. Check that ANTHROPIC_API_KEY is set and try again.")
                    else:
                        st.markdown("#### 🧠 AI Tutor")
                        st.markdown(f"**Step 1 — Why the correct answer is right:**\n\n{explanation['step1']}")
                        st.markdown(f"**Step 2 — Why your answer was wrong:**\n\n{explanation['step2']}")
                        st.markdown(f"**Step 3 — How to tell them apart:**\n\n{explanation['step3']}")
                        st.info(f"💡 Memory tip: {explanation['memory_tip']}")
                        st.markdown(f"**Follow-up question:** {explanation['follow_up']}")
                else:
                    if st.button("🧠 Get AI Explanation", key=f"tutor_btn_{item['id']}"):
                        with st.spinner("AI Tutor is thinking..."):
                            explanation = get_ai_tutor_explanation(
                                question=item,
                                selected_answer=item["selected_answer"],
                                correct_answer=item["correct_answer"],
                                domain=item["domain"],
                                topic=item["topic"],
                            )
                        st.session_state[tutor_cache_key] = explanation
                        if not st.session_state.get(tutor_xp_key):
                            add_xp(5, "Opened AI Tutor")
                            st.session_state[tutor_xp_key] = True
                        st.rerun()


def _render_quiz_form(quiz_key: str, result_key: str, title: str, save_mode: str, show_exam_breakdown: bool) -> None:
    payload = st.session_state.get(quiz_key)
    if not payload:
        st.info(f"{title} is not active. Generate one to begin.")
        return

    questions = payload["questions"]
    started_at = datetime.fromisoformat(payload["started_at"])
    timed_mode = payload["timed_mode"]
    minutes = payload["minutes"]
    exam = payload["exam"]
    payload.setdefault("answers", {})

    if timed_mode and minutes:
        ends_at = payload["ends_at"]
        remaining = max(0, int((datetime.fromisoformat(ends_at) - datetime.now()).total_seconds()))
        st.components.v1.html(countdown_html(ends_at), height=68)
        if remaining <= 0:
            st.error("Time has expired. Submit now to score the attempt.")

    answers = {}
    for index, question in enumerate(questions, start=1):
        widget_key = f"{quiz_key}_{payload['session_id']}_{index}"
        prior_answer = payload["answers"].get(question["id"])
        if widget_key not in st.session_state and prior_answer is not None:
            st.session_state[widget_key] = prior_answer
        current_answer = st.session_state.get(widget_key)
        answers[question["id"]] = current_answer

    if answers != payload["answers"]:
        payload["answers"] = answers.copy()
        _persist_session(quiz_key)

    answered_count = sum(1 for answer in answers.values() if answer)
    progress_ratio = answered_count / max(1, len(questions))
    st.progress(progress_ratio, text=f"{answered_count}/{len(questions)} answered")

    elapsed_minutes = max(1.0, (datetime.now() - started_at).total_seconds() / 60)
    pace = answered_count / elapsed_minutes
    projected_finish = round(len(questions) / max(pace, 0.01))

    insight_cols = st.columns(3)
    with insight_cols[0]:
        render_metric_card("Progress", f"{answered_count}/{len(questions)}", f"{_storage_caption()} while you work")
    with insight_cols[1]:
        render_metric_card("Pace", f"{pace:.1f}/min", "Current answering speed")
    with insight_cols[2]:
        render_metric_card("Projected Finish", f"{projected_finish} min", "Based on current pace")

    if len(questions) >= 100:
        render_insight_card(
            "Fatigue Simulation",
            f"This is the full endurance mode. Answers are {_storage_caption().lower()}, so you can resume the session if you need to step away.",
            pills=["100-question load", "Resume supported", "Recovery summary enabled"],
            warning=True,
        )
    elif len(questions) >= 75:
        render_insight_card(
            "Long Session",
            f"You are in a higher-volume drill. Progress, pacing, and in-progress answers are {_storage_caption().lower()}.",
            pills=["Pacing matters", "Resume supported"],
        )

    for index, question in enumerate(questions, start=1):
        st.markdown("<div class='question-shell'>", unsafe_allow_html=True)
        st.markdown(f"<h4>Q{index}. {escape(question['stem'])}</h4>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='question-meta'>{escape(question['domain'])} • {escape(question['topic'])}</div>",
            unsafe_allow_html=True,
        )
        st.radio(
            "Select one answer",
            question["options"],
            key=f"{quiz_key}_{payload['session_id']}_{index}",
            index=None,
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    button_cols = st.columns(2)
    with button_cols[0]:
        submitted = st.button("Submit Attempt", type="primary", use_container_width=True, key=f"{quiz_key}_submit")
    with button_cols[1]:
        save_only = st.button("Save And Resume Later", use_container_width=True, key=f"{quiz_key}_save")

    if save_only:
        payload["answers"] = {
            question["id"]: st.session_state.get(f"{quiz_key}_{payload['session_id']}_{index}")
            for index, question in enumerate(questions, start=1)
        }
        _persist_session(quiz_key)
        st.success(f"Session progress saved. Use the sidebar resume section to continue later. {_storage_caption()}.")

    if submitted:
        final_answers = {
            question["id"]: st.session_state.get(f"{quiz_key}_{payload['session_id']}_{index}")
            for index, question in enumerate(questions, start=1)
        }
        evaluated = evaluate_submission(questions, final_answers)
        elapsed_seconds = int((datetime.now() - started_at).total_seconds())
        result = {
            "exam": exam,
            "mode": save_mode,
            "question_count": len(questions),
            "correct_count": evaluated["correct_count"],
            "score_pct": evaluated["score_pct"],
            "timed_mode": timed_mode,
            "minutes_allocated": minutes,
            "elapsed_seconds": elapsed_seconds,
            "started_at": payload["started_at"],
            "submitted_at": datetime.now().isoformat(),
            "domain_breakdown": evaluated["domain_breakdown"],
            "topic_results": evaluated["topic_results"],
            "questions": evaluated["review"],
        }
        save_quiz_result(result)
        _clear_session(quiz_key)
        profile = _refresh_profile()
        st.session_state[result_key] = result
        all_results_now = load_results()
        _sync_mobile_data(profile, all_results_now)
        # Run misconception detection in the background (silent — results show in dashboard)
        try:
            detect_misconceptions(exam, all_results_now)
        except Exception:
            pass
        st.success(f"Scored {result['score_pct']:.1f}% ({result['correct_count']}/{result['question_count']}).")
        xp_result = award_quiz_xp(
            evaluated,
            result["score_pct"],
            elapsed_seconds,
            len(questions),
            hour=datetime.now().hour,
        )
        if xp_result["xp_earned"] > 0:
            st.info(f"+ {xp_result['xp_earned']:,} XP earned!")
        for badge_name in xp_result["badges_earned"]:
            st.success(f"🏅 Badge unlocked: **{badge_name}**")

    result = st.session_state.get(result_key)
    if result:
        _render_result_review(result, show_exam_breakdown)
