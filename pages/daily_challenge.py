from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from exams import EXAM_DOMAINS, get_question_pool
from storage import (
    add_xp,
    award_badge,
    get_badges,
    get_challenge_leaderboard,
    get_challenge_streak,
    get_daily_challenge,
    save_daily_challenge,
    update_challenge_streak,
    load_user_profile,
)
from utils import render_section_note


_STAR_RATINGS = ["☆☆☆☆☆", "★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"]
_DAILY_COUNT = 5


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def _generate_daily_questions(today_str: str) -> list[dict]:
    """Build 5 questions seeded by date — same for everyone each day."""
    pool: list[dict] = []
    for exam in EXAM_DOMAINS:
        for fact in get_question_pool(exam):
            pool.append({**fact, "exam": exam})

    if not pool:
        return []

    seed = int(today_str.replace("-", ""))
    rng = random.Random(seed)
    chosen = rng.sample(pool, min(_DAILY_COUNT, len(pool)))

    questions = []
    for fact in chosen:
        distractors = fact.get("distractors", [])
        options = [fact["correct"], *rng.sample(distractors, k=min(3, len(distractors)))]
        rng.shuffle(options)
        questions.append({
            "id": str(uuid.uuid4()),
            "exam": fact["exam"],
            "domain": fact["domain"],
            "topic": fact["concept"],
            "stem": (
                f"Which statement is correct about **{fact['concept']}**?  "
                f"*(Exam: {fact['exam']} | Domain: {fact['domain']})*"
            ),
            "options": options,
            "correct_answer": fact["correct"],
            "explanation": fact["explanation"],
        })
    return questions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _time_until_midnight() -> str:
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delta = tomorrow - now
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _award_challenge_xp(score: int, streak: int) -> tuple[int, list[str]]:
    xp = 0
    badges: list[str] = []
    existing = {b["badge_id"] for b in get_badges()}

    add_xp(100, "Daily Challenge completed")
    xp += 100

    if score == _DAILY_COUNT:
        add_xp(200, "Perfect Daily Challenge score")
        xp += 200
        if "perfectionist" not in existing:
            if award_badge("perfectionist", "Perfectionist", "Scored 5/5 on a Daily Challenge"):
                badges.append("Perfectionist")

    if "daily_champion" not in existing:
        if award_badge("daily_champion", "Daily Champion", "Completed your first Daily Challenge"):
            badges.append("Daily Champion")

    if streak >= 7:
        if "7_day_warrior" not in existing:
            add_xp(500, "7-day challenge streak bonus")
            xp += 500
            if award_badge("7_day_warrior", "7 Day Warrior", "Completed Daily Challenges 7 days in a row"):
                badges.append("7 Day Warrior")

    if streak >= 30:
        if "30_day_legend" not in existing:
            if award_badge("30_day_legend", "30 Day Legend", "Completed Daily Challenges 30 days in a row"):
                badges.append("30 Day Legend")

    return xp, badges


# ---------------------------------------------------------------------------
# Sub-renders
# ---------------------------------------------------------------------------

def _render_review(questions: list[dict], answers: dict) -> None:
    st.markdown("### Question Review")
    for i, q in enumerate(questions):
        selected = answers.get(q["id"])
        correct = q["correct_answer"]
        is_correct = selected == correct
        icon = "✅" if is_correct else "❌"
        with st.expander(
            f"{icon} Q{i + 1}: {q['topic']} ({q['exam']})",
            expanded=not is_correct,
        ):
            st.markdown(q["stem"])
            st.markdown(f"**Your answer:** {selected or '*(no answer)*'}")
            if not is_correct:
                st.markdown(f"**Correct answer:** {correct}")
            st.caption(f"Explanation: {q['explanation']}")


def _render_leaderboard(username: str) -> None:
    st.markdown("### Global Leaderboard")
    stats = get_challenge_leaderboard()
    if not stats:
        st.info("Complete today's challenge to appear on the leaderboard!")
        return

    st.markdown("**You are ranked #1 globally**")
    lb_df = pd.DataFrame([{
        "Rank": "#1",
        "Player": username,
        "Total Points": stats["total_pts"],
        "Challenges": stats["completed"],
        "Perfect Scores": stats["perfects"],
        "Best Streak": f"{stats['longest_streak']}d",
        "Current Streak": f"{stats['current_streak']}d",
    }])
    st.dataframe(lb_df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(ctx: dict) -> None:
    profile = ctx["profile"]
    today = date.today().isoformat()
    username = profile.get("name") or "You"

    st.subheader("Daily Challenge")
    render_section_note(
        "Five questions from across all certs, reset every midnight. "
        "The same questions for every player each day. "
        "Build a streak to earn bonus XP and exclusive badges."
    )

    streak = get_challenge_streak()
    completed_record = get_daily_challenge(today)

    # ── Header stats ─────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Challenge Streak", f"{streak['current_streak']} day{'s' if streak['current_streak'] != 1 else ''}")
    c2.metric("Longest Streak", f"{streak['longest_streak']} days")
    c3.metric("Next Reset In", _time_until_midnight(), help="Questions reset daily at midnight")
    st.divider()

    # ── Already completed ─────────────────────────────────────────────────────
    if completed_record:
        score = completed_record["score"]
        stars = _STAR_RATINGS[score]
        if score == _DAILY_COUNT:
            st.success(f"PERFECT SCORE! **{score}/{_DAILY_COUNT}** {stars} — today's challenge complete!")
            st.balloons()
        else:
            st.success(f"Today's challenge complete! You scored **{score}/{_DAILY_COUNT}** {stars}")

        # Show review if we still have the questions in session state
        if (
            st.session_state.get("dc_date") == today
            and st.session_state.get("dc_submitted")
        ):
            _render_review(
                st.session_state.get("dc_questions", []),
                st.session_state.get("dc_answers", {}),
            )

        st.divider()
        _render_leaderboard(username)
        return

    # ── Initialize session ────────────────────────────────────────────────────
    if st.session_state.get("dc_date") != today:
        st.session_state["dc_date"] = today
        st.session_state["dc_questions"] = _generate_daily_questions(today)
        st.session_state["dc_current"] = 0
        st.session_state["dc_answers"] = {}
        st.session_state["dc_phase"] = "playing"
        st.session_state["dc_submitted"] = False

    questions: list[dict] = st.session_state.get("dc_questions", [])
    if not questions:
        st.warning("No questions available — check that exam question banks are loaded.")
        return

    phase = st.session_state.get("dc_phase", "playing")

    # ── Review / award phase ──────────────────────────────────────────────────
    if phase == "review":
        answers = st.session_state.get("dc_answers", {})
        score = sum(
            1 for q in questions
            if answers.get(q["id"]) == q["correct_answer"]
        )
        perfect = score == _DAILY_COUNT

        # Persist + update streak + award XP
        save_daily_challenge(today, score, perfect)
        updated_streak = update_challenge_streak()
        xp, badges = _award_challenge_xp(score, updated_streak["current_streak"])
        st.session_state["dc_submitted"] = True

        stars = _STAR_RATINGS[score]
        if perfect:
            st.balloons()
            st.success(f"PERFECT SCORE! **{score}/{_DAILY_COUNT}** {stars} — +{xp:,} XP earned!")
        elif score >= 3:
            st.success(f"You scored **{score}/{_DAILY_COUNT}** {stars} — +{xp:,} XP earned!")
        else:
            st.warning(f"You scored **{score}/{_DAILY_COUNT}** {stars} — +{xp:,} XP earned. Keep practicing!")

        for b in badges:
            st.info(f"Badge unlocked: **{b}**!")

        _render_review(questions, answers)
        st.divider()
        _render_leaderboard(username)
        return

    # ── Playing phase — one question at a time ────────────────────────────────
    current_idx: int = st.session_state.get("dc_current", 0)
    # Guard against completed state reaching here
    if current_idx >= len(questions):
        st.session_state["dc_phase"] = "review"
        st.rerun()
        return

    progress = current_idx / len(questions)
    st.progress(progress, text=f"Question {current_idx + 1} of {len(questions)} — no going back")

    q = questions[current_idx]
    is_last = current_idx == len(questions) - 1

    with st.form(f"dc_q_{current_idx}", clear_on_submit=True):
        st.markdown(f"**Q{current_idx + 1} of {len(questions)}**")
        st.markdown(q["stem"])
        answer = st.radio(
            "Choose your answer:",
            q["options"],
            key=f"dc_radio_{current_idx}",
            index=None,
        )
        btn_label = "Submit All Answers" if is_last else "Next Question →"
        submitted = st.form_submit_button(btn_label, type="primary", use_container_width=True)

    if submitted:
        st.session_state["dc_answers"][q["id"]] = answer
        if is_last:
            st.session_state["dc_phase"] = "review"
        else:
            st.session_state["dc_current"] = current_idx + 1
        st.rerun()

    st.caption(
        f"Challenge streak: {streak['current_streak']} day(s) | "
        f"Complete all 5 to earn +100 XP | Perfect score earns +200 XP bonus"
    )
