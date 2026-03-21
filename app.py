from __future__ import annotations

from datetime import date, datetime, timedelta
from html import escape
import socket
from uuid import uuid4

import pandas as pd
import plotly.express as px
import streamlit as st

from auth import hash_passcode, is_locked_until, lockout_expiry_iso, passcode_feedback, verify_passcode
from exams import EXAM_DOMAINS, get_cheat_sheet, list_topics_for_exam
from labs import get_home_labs, lab_note_feedback
from question_engine import evaluate_submission, generate_quiz
from storage import (
    build_quiz_history_frame,
    default_profile,
    delete_active_session,
    ensure_storage,
    export_dataframe,
    export_markdown,
    load_active_sessions,
    load_results,
    load_user_profile,
    save_active_session,
    save_mobile_sync,
    save_quiz_result,
    save_user_profile,
)
from tracker import (
    build_mobile_sync_payload,
    build_markdown_study_summary,
    build_study_plan,
    calculate_readiness,
    confidence_by_domain,
    domain_breakdown,
    fatigue_breakdown,
    performance_over_time,
    predict_exam_score,
    readiness_history,
    recommend_study_next,
    recommended_next_topic,
    review_queue,
    strongest_topics,
    topic_history_frame,
    improved_topics,
    weakest_topics,
)
from utils import (
    apply_chart_style,
    countdown_html,
    default_minutes_for_exam,
    format_timestamp,
    inject_app_css,
    render_brand_ribbon,
    render_hero_panel,
    render_insight_card,
    render_metric_card,
    render_section_note,
    render_showcase_strip,
    render_topic_card,
)


st.set_page_config(page_title="NetSecure StudyOS", page_icon="🧠", layout="wide")
inject_app_css()
ensure_storage()


def _initialize_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("practice_quiz", None)
    st.session_state.setdefault("practice_result", None)
    st.session_state.setdefault("sim_quiz", None)
    st.session_state.setdefault("sim_result", None)


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


def _load_saved_sessions() -> None:
    sessions = load_active_sessions()
    session_by_mode = {
        "practice": "practice_quiz",
        "exam_simulator": "sim_quiz",
    }
    for session in sessions:
        key = session_by_mode.get(session.get("mode"))
        if key and st.session_state.get(key) is None:
            st.session_state[key] = session


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


def _save_onboarding(profile: dict, target_exam: str, target_date: date, weekly_hours: int, domain_ratings: dict[str, int]) -> dict:
    profile["onboarding_complete"] = True
    profile["target_exam"] = target_exam
    profile["target_date"] = target_date.isoformat()
    profile["weekly_study_hours"] = int(weekly_hours)
    profile.setdefault("domain_self_ratings", default_profile()["domain_self_ratings"])
    profile["domain_self_ratings"][target_exam] = domain_ratings
    save_user_profile(profile)
    return _refresh_profile()


def _save_lab_progress(
    profile: dict,
    exam: str,
    lab_id: str,
    completed_steps: list[int],
    total_steps: int,
    completion_note: str,
) -> dict:
    cleaned_note = completion_note.strip()[:2500]
    note_issues = lab_note_feedback(cleaned_note)
    is_complete = len(completed_steps) == total_steps and not note_issues
    profile.setdefault("lab_progress", {})
    profile["lab_progress"].setdefault(exam, {})
    profile["lab_progress"][exam][lab_id] = {
        "completed_steps": completed_steps,
        "completed": is_complete,
        "completion_note": cleaned_note,
        "note_requirements_met": not note_issues,
        "completed_at": datetime.now().isoformat() if is_complete else None,
    }
    save_user_profile(profile)
    return load_user_profile()


def _render_onboarding(profile: dict) -> dict:
    st.title("NetSecure StudyOS")
    st.caption("First-run onboarding personalizes readiness scoring, study plans, and recommendations.")
    render_section_note(
        "Set your target exam, target date, weekly study capacity, and confidence by domain. This stays local and tunes the app around your actual plan."
    )

    with st.form("first_run_onboarding", clear_on_submit=False):
        target_exam = st.selectbox("Target exam", list(EXAM_DOMAINS.keys()))
        target_date = st.date_input("Target exam date", value=date.today() + timedelta(days=45))
        weekly_hours = st.slider("Weekly study hours", min_value=1, max_value=30, value=int(profile.get("weekly_study_hours", 6)))
        st.markdown("### Self-Rated Confidence By Domain")
        st.caption("Rate each domain from 1 = very low confidence to 5 = very strong.")
        domain_ratings = {}
        existing = profile.get("domain_self_ratings", {}).get(target_exam, {})
        columns = st.columns(2)
        for index, domain in enumerate(EXAM_DOMAINS[target_exam]):
            with columns[index % 2]:
                domain_ratings[domain] = st.slider(
                    domain,
                    min_value=1,
                    max_value=5,
                    value=int(existing.get(domain, 3)),
                    key=f"onboarding_{target_exam}_{domain}",
                )
        submitted = st.form_submit_button("Save Profile And Start", type="primary", use_container_width=True)

    if submitted:
        if target_date <= date.today():
            st.error("Choose a target date in the future so the study plan can pace correctly.")
            return profile
        profile = _save_onboarding(profile, target_exam, target_date, weekly_hours, domain_ratings)
        st.success("Profile saved. Your dashboard is now personalized.")
        st.rerun()

    st.stop()


def _local_access_urls() -> tuple[str, str]:
    local_url = "http://localhost:8501"
    try:
        lan_ip = socket.gethostbyname(socket.gethostname())
        lan_url = f"http://{lan_ip}:8501"
    except OSError:
        lan_url = "Unavailable"
    return local_url, lan_url


def _render_passcode_setup(profile: dict) -> dict:
    st.title("NetSecure StudyOS")
    st.caption("Set a local passcode before enabling broader access.")
    render_section_note(
        "This passcode gate protects the app before you share it on your LAN or behind a public URL. The passcode is stored locally as a salted hash."
    )
    with st.form("passcode_setup_form", clear_on_submit=False):
        passcode = st.text_input("Create passcode", type="password")
        confirm_passcode = st.text_input("Confirm passcode", type="password")
        submitted = st.form_submit_button("Save Passcode And Continue", type="primary", use_container_width=True)
    if submitted:
        issues = passcode_feedback(passcode)
        if passcode != confirm_passcode:
            issues.append("Passcode confirmation does not match.")
        if issues:
            for issue in issues:
                st.error(issue)
        else:
            passcode_hash, passcode_salt = hash_passcode(passcode)
            profile["auth"]["passcode_hash"] = passcode_hash
            profile["auth"]["passcode_salt"] = passcode_salt
            profile["auth"]["failed_attempts"] = 0
            profile["auth"]["lockout_until"] = None
            profile["auth"]["updated_at"] = datetime.now().isoformat()
            save_user_profile(profile)
            st.session_state["authenticated"] = True
            st.success("Passcode saved.")
            st.rerun()
    st.stop()


def _require_passcode(profile: dict) -> dict:
    auth_state = profile.get("auth", {})
    passcode_hash = auth_state.get("passcode_hash")
    passcode_salt = auth_state.get("passcode_salt")
    if not passcode_hash or not passcode_salt:
        _render_passcode_setup(profile)

    if st.session_state.get("authenticated"):
        return profile

    if is_locked_until(auth_state.get("lockout_until")):
        st.title("NetSecure StudyOS")
        st.error(f"Too many failed attempts. Try again after {auth_state.get('lockout_until')}.")
        st.stop()

    st.title("NetSecure StudyOS")
    st.caption("Enter the local passcode to continue.")
    with st.form("passcode_unlock_form", clear_on_submit=False):
        passcode = st.text_input("Passcode", type="password")
        submitted = st.form_submit_button("Unlock", type="primary", use_container_width=True)
    if submitted:
        if verify_passcode(passcode, passcode_hash, passcode_salt):
            profile["auth"]["failed_attempts"] = 0
            profile["auth"]["lockout_until"] = None
            save_user_profile(profile)
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            failed_attempts = int(auth_state.get("failed_attempts", 0)) + 1
            profile["auth"]["failed_attempts"] = failed_attempts
            if failed_attempts >= 5:
                profile["auth"]["lockout_until"] = lockout_expiry_iso()
                profile["auth"]["failed_attempts"] = 0
            save_user_profile(profile)
            st.error("Incorrect passcode.")
    st.stop()


def _render_profile_editor(profile: dict) -> dict:
    with st.expander("Edit Study Profile"):
        exam_options = list(EXAM_DOMAINS.keys())
        current_target_exam = profile.get("target_exam") if profile.get("target_exam") in EXAM_DOMAINS else exam_options[0]
        current_target_date = profile.get("target_date")
        try:
            parsed_target_date = datetime.fromisoformat(current_target_date).date() if current_target_date else date.today() + timedelta(days=45)
        except ValueError:
            parsed_target_date = date.today() + timedelta(days=45)
        with st.form("edit_profile_form", clear_on_submit=False):
            target_exam = st.selectbox("Target exam", exam_options, index=exam_options.index(current_target_exam))
            target_date = st.date_input("Target exam date", value=parsed_target_date, key="edit_target_date")
            weekly_hours = st.slider(
                "Weekly study hours",
                min_value=1,
                max_value=30,
                value=int(profile.get("weekly_study_hours", 6)),
                key="edit_weekly_hours",
            )
            st.markdown("### Self-Rated Confidence By Domain")
            domain_ratings = {}
            existing = profile.get("domain_self_ratings", {}).get(target_exam, {})
            columns = st.columns(2)
            for index, domain in enumerate(EXAM_DOMAINS[target_exam]):
                with columns[index % 2]:
                    domain_ratings[domain] = st.slider(
                        domain,
                        min_value=1,
                        max_value=5,
                        value=int(existing.get(domain, 3)),
                        key=f"edit_{target_exam}_{domain}",
                    )
            submitted = st.form_submit_button("Update Profile", use_container_width=True)
        if submitted:
            if target_date <= date.today():
                st.error("Choose a target date in the future so the study plan can pace correctly.")
            else:
                profile = _save_onboarding(profile, target_exam, target_date, weekly_hours, domain_ratings)
                st.success("Study profile updated.")
                st.rerun()
    return profile


def _render_share_settings(profile: dict) -> dict:
    with st.expander("Access And Share Settings"):
        local_url, lan_url = _local_access_urls()
        st.write(f"Local URL: {local_url}")
        st.write(f"LAN URL: {lan_url}")
        st.caption("To make the app available to everybody, expose it through a trusted public host or tunnel and paste the resulting URLs below.")
        with st.form("share_links_form", clear_on_submit=False):
            public_app_url = st.text_input("Public app URL", value=profile.get("links", {}).get("public_app_url") or "")
            mobile_app_url = st.text_input("Mobile app URL", value=profile.get("links", {}).get("mobile_app_url") or "")
            submitted = st.form_submit_button("Save Share Links", use_container_width=True)
        if submitted:
            profile.setdefault("links", {})
            profile["links"]["public_app_url"] = public_app_url.strip() or None
            profile["links"]["mobile_app_url"] = mobile_app_url.strip() or None
            save_user_profile(profile)
            st.success("Share links saved.")
            st.rerun()
    return profile


def _render_saved_sessions_sidebar() -> None:
    sessions = load_active_sessions()
    if not sessions:
        return
    st.subheader("Resume Session")
    mode_to_key = {"practice": "practice_quiz", "exam_simulator": "sim_quiz"}
    for session in reversed(sessions):
        answered = sum(1 for value in session.get("answers", {}).values() if value)
        label = f"{session['exam']} • {session['label']}"
        st.caption(f"{label} • {answered}/{len(session.get('questions', []))} answered")
        action_cols = st.columns(2)
        with action_cols[0]:
            if st.button("Resume", key=f"resume_{session['session_id']}", use_container_width=True):
                st.session_state[mode_to_key[session["mode"]]] = session
        with action_cols[1]:
            if st.button("Discard", key=f"discard_{session['session_id']}", use_container_width=True):
                delete_active_session(session["session_id"])
                active_payload = st.session_state.get(mode_to_key[session["mode"]])
                if active_payload and active_payload.get("session_id") == session["session_id"]:
                    st.session_state[mode_to_key[session["mode"]]] = None
                st.rerun()


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
        render_metric_card("Progress", f"{answered_count}/{len(questions)}", "Saved locally while you work")
    with insight_cols[1]:
        render_metric_card("Pace", f"{pace:.1f}/min", "Current answering speed")
    with insight_cols[2]:
        render_metric_card("Projected Finish", f"{projected_finish} min", "Based on current pace")

    if len(questions) >= 100:
        render_insight_card(
            "Fatigue Simulation",
            "This is the full endurance mode. Answers persist locally, so you can resume the session if you need to step away.",
            pills=["100-question load", "Resume supported", "Recovery summary enabled"],
            warning=True,
        )
    elif len(questions) >= 75:
        render_insight_card(
            "Long Session",
            "You are in a higher-volume drill. Progress, pacing, and in-progress answers are all stored locally.",
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
        st.success("Session progress saved locally. Use the sidebar resume section to continue later.")

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
        _sync_mobile_data(profile, load_results())
        st.success(f"Scored {result['score_pct']:.1f}% ({result['correct_count']}/{result['question_count']}).")

    result = st.session_state.get(result_key)
    if result:
        _render_result_review(result, show_exam_breakdown)


def _export_section(selected_exam: str, all_results: list[dict], exam_results: list[dict]) -> None:
    st.markdown("### Power BI Export Prep")
    render_section_note(
        "Use these exports to feed Power BI locally. Files are written to data/exports so refreshes can point at a stable folder."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Export Quiz History", use_container_width=True):
            frame = build_quiz_history_frame(all_results)
            path = export_dataframe(frame, "quiz_history.csv")
            st.success(f"Saved {path.name} to data/exports.")
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
            st.success(f"Saved {path.name} to data/exports.")
    with c3:
        if st.button(f"Export {selected_exam} Readiness History", use_container_width=True):
            frame = readiness_history(selected_exam, exam_results)
            path = export_dataframe(
                frame,
                f"readiness_history_{selected_exam.lower().replace('+', 'plus').replace(' ', '_')}.csv",
            )
            st.success(f"Saved {path.name} to data/exports.")

    st.markdown("### Markdown Study Summary")
    render_section_note(
        "Create a polished markdown progress summary for GitHub, a portfolio repo, or a LinkedIn post draft."
    )
    if st.button("Export Markdown Study Summary", use_container_width=True):
        content = build_markdown_study_summary(all_results, load_user_profile())
        path = export_markdown(content, "study_summary.md")
        st.success(f"Saved {path.name} to data/exports.")


_initialize_state()
_load_saved_sessions()
profile = load_user_profile()
profile = _require_passcode(profile)

if not profile.get("onboarding_complete"):
    _render_onboarding(profile)

profile = _refresh_profile()

st.title("NetSecure StudyOS")
st.caption("A local-first study system for networking, cloud, and security certification prep.")

with st.sidebar:
    st.header("Session Setup")
    exam_options = list(EXAM_DOMAINS.keys())
    default_exam = profile.get("target_exam") if profile.get("target_exam") in EXAM_DOMAINS else exam_options[0]
    selected_exam = st.selectbox("Select exam", exam_options, index=exam_options.index(default_exam))
    selected_mode = st.selectbox("Select mode", ["Practice", "Exam Simulator"])
    selected_count = st.selectbox("Select question count", [10, 25, 50, 90, 100], index=1)
    timed_mode = st.toggle("Timed mode", value=False)
    default_minutes = default_minutes_for_exam(selected_count)
    minutes = st.number_input(
        "Minutes",
        min_value=5,
        max_value=240,
        value=default_minutes,
        step=5,
        disabled=not timed_mode,
    )
    st.divider()
    st.subheader("Target Plan")
    st.write(f"Exam: {profile.get('target_exam') or '-'}")
    st.write(f"Date: {profile.get('target_date') or '-'}")
    st.write(f"Weekly hours: {profile.get('weekly_study_hours', 0)}")
    st.divider()
    st.subheader("Exam Readiness")
    readiness_value = profile.get("exam_readiness", {}).get(selected_exam, 36.0)
    st.progress(min(int(readiness_value), 100))
    st.write(f"{readiness_value:.1f}/100")
    st.caption("Practice mode is better for weak-topic cleanup. Simulator mode is better for pacing, fatigue, and score validation.")
    st.divider()
    _render_profile_editor(profile)
    st.divider()
    _render_share_settings(profile)
    st.divider()
    _render_saved_sessions_sidebar()
    if st.button("Lock App", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

all_results = load_results()
exam_results = load_results(selected_exam)
current_readiness = calculate_readiness(selected_exam, exam_results, profile)
current_latest_score = exam_results[-1]["score_pct"] if exam_results else 0.0
prediction = predict_exam_score(selected_exam, exam_results, profile)
recommended = recommended_next_topic(selected_exam, exam_results, profile)
domain_conf_df = confidence_by_domain(selected_exam, exam_results)
queue_df = review_queue(selected_exam, exam_results)
history_df = topic_history_frame(selected_exam, exam_results)
study_hours = int(profile.get("weekly_study_hours", 8) or 8)

render_brand_ribbon(
    [
        (f"Target: {profile.get('target_exam') or selected_exam}", False),
        (f"Weekly Hours: {study_hours}", False),
        (f"{len(EXAM_DOMAINS)} Certifications", True),
        ("Local-First Analytics", True),
    ]
)
render_hero_panel(selected_exam, selected_mode, current_readiness, current_latest_score, len(exam_results))
render_showcase_strip(
    [
        {
            "label": "Current Momentum",
            "value": f"{current_latest_score:.1f}%",
            "detail": "Latest scored performance snapshot",
        },
        {
            "label": "Next Best Move",
            "value": recommended["topic"],
            "detail": recommended["domain"],
        },
        {
            "label": "Forecast Window",
            "value": f"{prediction['range_low']:.0f}-{prediction['range_high']:.0f}%",
            "detail": prediction["confidence_note"],
        },
    ]
)

tabs = st.tabs(
    [
        "Dashboard",
        "Quiz Generator",
        "Exam Simulator",
        "Weak Topics",
        "Study Plan",
        "Cheat Sheets",
        "Predicted Score",
        "Review Queue",
        "Home Labs",
    ]
)
dashboard_tab, quiz_tab, simulator_tab, weak_tab, plan_tab, cheat_tab, prediction_tab, review_tab, labs_tab = tabs

with dashboard_tab:
    weakest = weakest_topics(selected_exam, exam_results, limit=5)
    strongest = strongest_topics(selected_exam, exam_results, limit=5)
    metrics = st.columns(4)
    with metrics[0]:
        render_metric_card("Readiness Score", f"{current_readiness:.1f}", "Personalized by profile and history")
    with metrics[1]:
        render_metric_card("Total Attempts", str(len(exam_results)), "Saved locally")
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
    _export_section(selected_exam, all_results, exam_results)

with quiz_tab:
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

with simulator_tab:
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

with weak_tab:
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

with plan_tab:
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

with cheat_tab:
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

with prediction_tab:
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

with review_tab:
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

with labs_tab:
    st.subheader("Hands-On Home Labs")
    render_section_note(
        "Use these guided labs to turn certification concepts into practical experience. Resume bullets stay locked until every step in a lab is marked complete and saved."
    )
    labs = get_home_labs(selected_exam)
    if not labs:
        st.info("No home labs are defined for this exam yet.")
    for index, lab in enumerate(labs, start=1):
        progress = profile.get("lab_progress", {}).get(selected_exam, {}).get(lab["id"], {})
        completed_steps = progress.get("completed_steps", [])
        completion_note = progress.get("completion_note", "")
        is_complete = (
            bool(progress.get("completed"))
            and len(completed_steps) == len(lab["steps"])
            and not lab_note_feedback(completion_note)
        )
        render_topic_card(
            f"Lab {index} • {lab['title']}",
            [f"Why this lab matters: {lab['why']}"],
            pills=[selected_exam, "Hands-on", "Completed" if is_complete else "In progress"],
        )
        st.markdown("### Step-By-Step Directions")
        updated_steps: list[int] = []
        for step_number, step in enumerate(lab["steps"], start=1):
            checked = st.checkbox(
                f"{step_number}. {step}",
                value=step_number in completed_steps,
                key=f"{lab['id']}_step_{step_number}",
            )
            if checked:
                updated_steps.append(step_number)

        action_cols = st.columns(2)
        note_value = st.text_area(
            "Completion Reflection / Evidence Note",
            value=completion_note,
            key=f"{lab['id']}_note",
            help="Use this exact rubric: `Built:`, `Verified:`, and `Evidence:`. The bullets unlock only after all sections are present and the note is substantive.",
            placeholder=(
                "Built: Created the VLAN and routing lab in Packet Tracer.\n"
                "Verified: Tested inter-VLAN routing with ping and show commands.\n"
                "Evidence: Saved screenshots of trunks, ACL denies, and DHCP leases."
            ),
        )
        with action_cols[0]:
            if st.button("Save Lab Progress", key=f"save_lab_{lab['id']}", use_container_width=True):
                profile = _save_lab_progress(
                    profile,
                    selected_exam,
                    lab["id"],
                    updated_steps,
                    len(lab["steps"]),
                    note_value,
                )
                current_issues = lab_note_feedback(note_value)
                if len(updated_steps) == len(lab["steps"]) and not current_issues:
                    st.success("Lab marked complete. Resume bullets are now unlocked.")
                elif len(updated_steps) == len(lab["steps"]):
                    st.warning("All steps are complete, but the reflection/evidence note still does not meet the unlock rubric.")
                else:
                    st.success("Lab progress saved. Complete every step and add a reflection/evidence note to unlock the resume bullets.")
                st.rerun()
        with action_cols[1]:
            st.progress(len(updated_steps) / max(1, len(lab["steps"])), text=f"{len(updated_steps)}/{len(lab['steps'])} steps complete")

        current_note_issues = lab_note_feedback(note_value)
        if current_note_issues:
            st.caption("Unlock rubric:")
            for issue in current_note_issues:
                st.write(f"- {issue}")
        else:
            st.caption("Reflection/evidence note requirement met.")

        st.markdown("### Resume Bullets")
        if is_complete:
            st.markdown("### Completion Reflection")
            st.write(completion_note)
            for bullet in lab["resume_bullets"]:
                st.write(f"- {bullet}")
        else:
            st.info("Complete and save every step in this lab and satisfy the Built / Verified / Evidence reflection rubric to unlock the resume bullets.")
