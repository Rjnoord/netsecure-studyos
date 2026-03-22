from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta

import streamlit as st

from exams import EXAM_DOMAINS, get_question_pool
from question_engine import generate_quiz
from storage import (
    add_xp,
    award_badge,
    get_badges,
    get_boss_battle_stats,
    get_debate_history,
    get_debate_stats,
    save_boss_battle,
    save_debate_session,
)
from utils import countdown_html, render_section_note
from pages._shared import _build_quiz_session, _persist_session, _render_quiz_form


# ---------------------------------------------------------------------------
# Debate Mode helpers
# ---------------------------------------------------------------------------

_DEBATE_MIN_WORDS = 50


def _pick_debate_question(exam: str) -> dict | None:
    """Return a random question from the pool with a selected wrong answer."""
    import random
    pool = get_question_pool(exam)
    if not pool:
        return None
    fact = random.choice(pool)
    distractors = fact.get("distractors", [])
    if not distractors:
        return None
    wrong = random.choice(distractors)
    return {
        "exam": exam,
        "domain": fact["domain"],
        "topic": fact["concept"],
        "correct_answer": fact["correct"],
        "wrong_answer": wrong,
        "explanation": fact["explanation"],
    }


def _grade_debate_response(
    exam: str,
    domain: str,
    topic: str,
    wrong_answer: str,
    correct_answer: str,
    user_response: str,
) -> dict | None:
    """Ask Claude to grade the user's written rebuttal."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": (
                    f"You are grading a written technical rebuttal for the {exam} exam.\n\n"
                    f"Domain: {domain}\n"
                    f"Topic: {topic}\n"
                    f"Wrong answer presented to the student: {wrong_answer}\n"
                    f"Correct answer: {correct_answer}\n\n"
                    f"Student's rebuttal:\n{user_response}\n\n"
                    "Grade the response on these three dimensions and return ONLY a JSON object with:\n"
                    '- "score": integer 1-10 (overall grade)\n'
                    '- "technical_accuracy": string (1-2 sentences — is their reasoning correct?)\n'
                    '- "completeness": string (1-2 sentences — did they identify the real answer?)\n'
                    '- "clarity": string (1-2 sentences — would a colleague understand it?)\n'
                    '- "model_answer": string (2-3 sentences — ideal rebuttal for comparison)\n'
                    '- "feedback": string (1-2 sentences of specific actionable advice)\n'
                    "Output only valid JSON, no markdown fences."
                ),
            }],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        grade = __import__("json").loads(text)
        required = {"score", "technical_accuracy", "completeness", "clarity", "model_answer", "feedback"}
        return grade if required.issubset(grade.keys()) else None
    except Exception:
        return None


def _award_debate_xp(score: int, domain: str) -> tuple[int, list[str]]:
    xp = 0
    badges: list[str] = []
    existing = {b["badge_id"] for b in get_badges()}

    add_xp(30, "Debate completed")
    xp += 30

    if score >= 8:
        add_xp(75, "Debate high score (8+/10)")
        xp += 75

    if "debater" not in existing:
        if award_badge("debater", "Debater", "Completed your first Debate session"):
            badges.append("Debater")

    # Check for Eloquent badge (10 debates scored 8+)
    stats = get_debate_stats()
    if stats["high_scores"] >= 10 and "eloquent" not in existing:
        if award_badge("eloquent", "Eloquent", "Scored 8+ on 10 Debate sessions"):
            badges.append("Eloquent")

    # Check for Domain Expert badge (5 perfect 10/10 in same domain)
    if score == 10:
        history = get_debate_history(limit=50)
        domain_perfects = sum(1 for s in history if s.get("domain") == domain and s.get("score") == 10)
        if domain_perfects >= 5 and "domain_expert" not in existing:
            if award_badge("domain_expert", "Domain Expert", f"Scored 10/10 on 5 Debate sessions in {domain}"):
                badges.append("Domain Expert")

    return xp, badges


def _render_debate_mode(exam: str) -> None:
    """Debate Mode state machine rendered inline."""
    st.divider()
    st.subheader("Debate Mode")
    render_section_note(
        "A colleague is wrong on the internet — and it's your job to correct them. "
        "We'll present a wrong answer as if it's correct. Write a rebuttal (50+ words) "
        "explaining why they're mistaken and what the real answer is."
    )

    phase = st.session_state.get("debate_phase", "idle")
    debate_exam = st.session_state.get("debate_exam")

    # Reset if switching exam
    if debate_exam != exam and phase != "idle":
        st.session_state["debate_phase"] = "idle"
        phase = "idle"

    stats = get_debate_stats()
    if stats["total"] > 0:
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Debates Completed", stats["total"])
        sc2.metric("Average Score", f"{stats['avg_score']}/10")
        sc3.metric("Strongest Domain", stats["strongest_domain"])

    # ── Idle ─────────────────────────────────────────────────────────────────
    if phase == "idle":
        if st.button("Start Debate", type="primary", use_container_width=True, key="debate_start"):
            q = _pick_debate_question(exam)
            if not q:
                st.error("No questions available for this exam.")
                return
            st.session_state.update({
                "debate_exam": exam,
                "debate_q": q,
                "debate_phase": "writing",
                "debate_grade": None,
                "debate_xp_key": None,
            })
            st.rerun()
        return

    # ── Writing phase ─────────────────────────────────────────────────────────
    if phase == "writing":
        q = st.session_state.get("debate_q", {})
        st.markdown(
            f"**Domain:** {q.get('domain')} &nbsp;|&nbsp; "
            f"**Topic:** {q.get('topic')} &nbsp;|&nbsp; "
            f"**Exam:** {q.get('exam')}"
        )
        st.warning(
            f"Your colleague says: **\"{q.get('wrong_answer')}\"**\n\n"
            "Explain in writing why they are incorrect and what the right answer actually is."
        )

        with st.form("debate_form"):
            response = st.text_area(
                "Your rebuttal (minimum 50 words):",
                height=180,
                key="debate_response_input",
                placeholder="Type your technical explanation here...",
            )
            word_count = len(response.split()) if response else 0
            submitted = st.form_submit_button("Submit Rebuttal", type="primary", use_container_width=True)

        st.caption(f"Word count: {word_count} / {_DEBATE_MIN_WORDS} minimum")

        if submitted:
            if word_count < _DEBATE_MIN_WORDS:
                st.error(f"Response too short — write at least {_DEBATE_MIN_WORDS} words ({word_count} so far).")
            else:
                st.session_state["debate_user_response"] = response
                st.session_state["debate_phase"] = "grading"
                st.rerun()
        return

    # ── Grading phase ─────────────────────────────────────────────────────────
    if phase == "grading":
        q = st.session_state.get("debate_q", {})
        response = st.session_state.get("debate_user_response", "")

        if not st.session_state.get("debate_grade"):
            with st.spinner("Grading your rebuttal..."):
                grade = _grade_debate_response(
                    q.get("exam", exam),
                    q.get("domain", ""),
                    q.get("topic", ""),
                    q.get("wrong_answer", ""),
                    q.get("correct_answer", ""),
                    response,
                )
            if not grade:
                grade = {
                    "score": 5,
                    "technical_accuracy": "Unable to grade — check ANTHROPIC_API_KEY.",
                    "completeness": "Unable to grade.",
                    "clarity": "Unable to grade.",
                    "model_answer": q.get("explanation", "See exam documentation."),
                    "feedback": "Resubmit when the API connection is restored.",
                }
            st.session_state["debate_grade"] = grade

        grade = st.session_state["debate_grade"]
        score = grade.get("score", 5)

        # Award XP once
        xp_key = f"debate_xp_{id(st.session_state.get('debate_q', {}))}"
        if not st.session_state.get(xp_key):
            xp, new_badges = _award_debate_xp(score, q.get("domain", ""))
            save_debate_session(
                exam=q.get("exam", exam),
                domain=q.get("domain", ""),
                topic=q.get("topic", ""),
                wrong_answer=q.get("wrong_answer", ""),
                user_response=response,
                score=score,
            )
            st.session_state[xp_key] = True
            st.session_state["debate_xp_earned"] = xp
            st.session_state["debate_new_badges"] = new_badges

        # Result display
        if score >= 8:
            st.success(f"Score: **{score}/10** — Excellent rebuttal!")
        elif score >= 5:
            st.warning(f"Score: **{score}/10** — Solid effort, see feedback below.")
        else:
            st.error(f"Score: **{score}/10** — Needs work.")

        xp_earned = st.session_state.get("debate_xp_earned", 0)
        if xp_earned:
            st.info(f"+{xp_earned:,} XP earned!")
        for b in st.session_state.get("debate_new_badges", []):
            st.success(f"Badge unlocked: **{b}**!")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Technical Accuracy**")
            st.write(grade.get("technical_accuracy", ""))
            st.markdown("**Completeness**")
            st.write(grade.get("completeness", ""))
        with col2:
            st.markdown("**Clarity**")
            st.write(grade.get("clarity", ""))
            st.markdown("**Feedback**")
            st.write(grade.get("feedback", ""))

        st.markdown("**Model Answer (for comparison)**")
        st.info(grade.get("model_answer", ""))
        st.markdown(f"*Correct answer: {q.get('correct_answer', '')}*")

        if st.button("Next Debate", use_container_width=True, key="debate_next"):
            st.session_state["debate_phase"] = "idle"
            st.session_state.pop("debate_grade", None)
            st.session_state.pop("debate_user_response", None)
            st.rerun()
        return


# ---------------------------------------------------------------------------
# Boss Battle helpers
# ---------------------------------------------------------------------------

def _generate_battle_questions(exam: str, count: int = 10) -> list[dict]:
    """Pull count questions from the full question pool for the given exam."""
    pool = get_question_pool(exam)
    if not pool:
        return []
    rng = __import__("random").Random()
    chosen = rng.sample(pool, min(count, len(pool)))
    questions = []
    for fact in chosen:
        distractors = fact.get("distractors", [])
        options = [fact["correct"], *rng.sample(distractors, k=min(3, len(distractors)))]
        rng.shuffle(options)
        questions.append({
            "id": str(uuid.uuid4()),
            "exam": exam,
            "domain": fact["domain"],
            "topic": fact["concept"],
            "stem": f"Which statement is correct about **{fact['concept']}**?",
            "options": options,
            "correct_answer": fact["correct"],
            "explanation": fact["explanation"],
        })
    return questions


def _call_hiring_manager(exam: str, score: int, weak_answers: list[dict]) -> list[str] | None:
    """Ask Claude to generate 3 technical follow-up questions as a hiring manager."""
    try:
        import anthropic
        client = anthropic.Anthropic()

        missed_text = "\n".join(
            f"- Topic: {q['topic']} | Domain: {q['domain']} | Correct: {q['correct_answer']}"
            for q in weak_answers[:4]
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a senior hiring manager interviewing a candidate for a {exam} role. "
                    f"The candidate scored {score}/10 on a rapid-fire technical quiz. "
                    f"Their weakest areas were:\n{missed_text}\n\n"
                    "Ask 3 technical follow-up questions targeting their 2 weakest answers. "
                    "Be direct and professional. "
                    "Return ONLY a JSON array with exactly 3 question strings, no other text."
                ),
            }],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        # Strip markdown fences if present
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        questions = json.loads(text)
        if isinstance(questions, list) and len(questions) >= 3:
            return [str(q) for q in questions[:3]]
        return None
    except Exception:
        return None


def _call_grade_responses(
    exam: str,
    interview_qs: list[str],
    responses: dict[int, str],
) -> dict | None:
    """Ask Claude to grade the candidate's interview responses."""
    try:
        import anthropic
        client = anthropic.Anthropic()

        qa_parts = []
        for i, q in enumerate(interview_qs):
            ans = responses.get(i, "").strip() or "(no response)"
            qa_parts.append(f"Q{i+1}: {q}\nA{i+1}: {ans}")
        qa_text = "\n\n".join(qa_parts)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a senior hiring manager evaluating a candidate for a {exam} role. "
                    f"Grade their responses to these 3 technical interview questions:\n\n{qa_text}\n\n"
                    "Return ONLY a JSON object with exactly these keys:\n"
                    '- "score": integer 1-10\n'
                    '- "technical_accuracy": string (1-2 sentences)\n'
                    '- "communication_clarity": string (1-2 sentences)\n'
                    '- "hiring_recommendation": one of "Strong Yes", "Yes", "Maybe", "No"\n'
                    '- "feedback": string (2-3 sentences of actionable feedback)\n'
                    "Output only valid JSON, no markdown fences."
                ),
            }],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        grade = json.loads(text)
        required = {"score", "technical_accuracy", "communication_clarity", "hiring_recommendation", "feedback"}
        if required.issubset(grade.keys()):
            return grade
        return None
    except Exception:
        return None


def _award_battle_xp(score: int, hiring_rec: str) -> tuple[int, list[str]]:
    xp = 0
    badges: list[str] = []
    existing = {b["badge_id"] for b in get_badges()}

    add_xp(300, "Boss Battle completed")
    xp += 300

    if score >= 8:
        add_xp(200, "Boss Battle high score (8+/10)")
        xp += 200

    if hiring_rec == "Strong Yes":
        add_xp(500, "Hiring recommendation: Strong Yes")
        xp += 500
        if "interview_ready" not in existing:
            if award_badge("interview_ready", "Interview Ready", "Received a Strong Yes hiring recommendation"):
                badges.append("Interview Ready")

    if "boss_slayer" not in existing:
        if award_badge("boss_slayer", "Boss Slayer", "Completed your first Boss Battle"):
            badges.append("Boss Slayer")

    # Check consecutive 8+ scores
    stats = get_boss_battle_stats()
    if stats["high_scores"] >= 3 and "undefeated" not in existing:
        if award_badge("undefeated", "Undefeated", "Scored 8+ on 3 consecutive Boss Battles"):
            badges.append("Undefeated")

    return xp, badges


# ---------------------------------------------------------------------------
# Boss Battle render
# ---------------------------------------------------------------------------

_BATTLE_TOTAL_SECONDS = 90
_BATTLE_QUESTION_COUNT = 10


def _render_boss_battle(exam: str, current_readiness: float) -> None:
    """Full Boss Battle state machine rendered inline."""
    st.divider()
    st.subheader("Boss Battle Mode")

    if current_readiness < 70:
        st.info(
            f"Boss Battle unlocks at 70% readiness. "
            f"Your current readiness for {exam} is **{current_readiness:.1f}%**. "
            "Keep practicing to unlock this mode!"
        )
        return

    st.success(
        f"Readiness: **{current_readiness:.1f}%** — Boss Battle unlocked for {exam}!"
    )
    render_section_note(
        "10 rapid-fire questions. 90-second countdown for all of them. "
        "No explanations during the battle. "
        "Survive and face the Hiring Manager."
    )

    phase = st.session_state.get("bb_phase")
    bb_exam = st.session_state.get("bb_exam")

    # Reset if switching exam
    if bb_exam != exam and phase is not None:
        st.session_state["bb_phase"] = None
        phase = None

    # ── Idle ─────────────────────────────────────────────────────────────────
    if phase is None:
        stats = get_boss_battle_stats()
        if stats["total"] > 0:
            c1, c2, c3 = st.columns(3)
            c1.metric("Battles Fought", stats["total"])
            c2.metric("Best Score", f"{stats['best_score']}/10")
            c3.metric("Best Recommendation", stats["best_rec"] or "—")

        if st.button("Enter Boss Battle", type="primary", use_container_width=True, key="bb_start"):
            questions = _generate_battle_questions(exam, _BATTLE_QUESTION_COUNT)
            if not questions:
                st.error("Not enough questions in the bank for this exam.")
                return
            ends_at = (datetime.now() + timedelta(seconds=_BATTLE_TOTAL_SECONDS)).isoformat()
            st.session_state.update({
                "bb_exam": exam,
                "bb_phase": "playing",
                "bb_questions": questions,
                "bb_current": 0,
                "bb_answers": {},
                "bb_ends_at": ends_at,
                "bb_result": None,
                "bb_interview_qs": None,
                "bb_responses": {},
                "bb_grade": None,
            })
            st.rerun()
        return

    # ── Playing phase ─────────────────────────────────────────────────────────
    if phase == "playing":
        questions: list[dict] = st.session_state["bb_questions"]
        ends_at: str = st.session_state["bb_ends_at"]
        current_idx: int = st.session_state.get("bb_current", 0)

        remaining = max(0, int(
            (datetime.fromisoformat(ends_at) - datetime.now()).total_seconds()
        ))

        # Timer display — red when urgent
        if remaining <= 30:
            st.error(f"TIME RUNNING OUT: {remaining}s remaining!")
        else:
            st.components.v1.html(countdown_html(ends_at), height=68)

        # Auto-submit if time expired
        if remaining <= 0:
            st.session_state["bb_phase"] = "review"
            st.rerun()
            return

        # Progress
        total = len(questions)
        st.progress(current_idx / total, text=f"Question {current_idx + 1} of {total}")

        q = questions[current_idx]
        is_last = current_idx == total - 1

        with st.form(f"bb_q_{current_idx}", clear_on_submit=True):
            st.markdown(f"**Q{current_idx + 1}:** {q['stem']}")
            st.caption(f"Domain: {q['domain']}")
            answer = st.radio(
                "Answer:",
                q["options"],
                key=f"bb_radio_{current_idx}",
                index=None,
            )
            btn = "Finish Battle" if is_last else "Next →"
            go = st.form_submit_button(btn, type="primary", use_container_width=True)

        if go:
            # Re-check time on submit
            remaining_now = max(0, int(
                (datetime.fromisoformat(ends_at) - datetime.now()).total_seconds()
            ))
            st.session_state["bb_answers"][q["id"]] = answer
            if is_last or remaining_now <= 0:
                st.session_state["bb_phase"] = "review"
            else:
                st.session_state["bb_current"] = current_idx + 1
            st.rerun()

        # Live timer refresh every second during battle
        time.sleep(1)
        st.rerun()
        return

    # ── Review phase ──────────────────────────────────────────────────────────
    if phase == "review":
        questions = st.session_state["bb_questions"]
        answers = st.session_state.get("bb_answers", {})

        correct_count = sum(
            1 for q in questions if answers.get(q["id"]) == q["correct_answer"]
        )
        score = correct_count
        total = len(questions)
        wrong_qs = [q for q in questions if answers.get(q["id"]) != q["correct_answer"]]

        # Score display
        pct = round((score / total) * 100)
        if score >= 8:
            st.success(f"BOSS DEFEATED! **{score}/{total}** ({pct}%) — Outstanding!")
        elif score >= 5:
            st.warning(f"Battle complete: **{score}/{total}** ({pct}%) — Needs improvement.")
        else:
            st.error(f"Battle lost: **{score}/{total}** ({pct}%) — Keep training!")

        # Question breakdown (no explanations during battle review — shown after interview)
        with st.expander("Battle Breakdown", expanded=True):
            for i, q in enumerate(questions):
                sel = answers.get(q["id"])
                icon = "✅" if sel == q["correct_answer"] else "❌"
                st.markdown(f"{icon} Q{i+1}: {q['topic']} ({q['domain']})")

        st.session_state["bb_result"] = {"score": score, "total": total, "wrong_qs": wrong_qs}

        # Trigger interview
        if st.button("Face the Hiring Manager", type="primary", use_container_width=True, key="bb_to_interview"):
            st.session_state["bb_phase"] = "interview"
            st.rerun()
        return

    # ── Interview phase ────────────────────────────────────────────────────────
    if phase == "interview":
        result = st.session_state.get("bb_result", {})
        score = result.get("score", 0)
        total = result.get("total", _BATTLE_QUESTION_COUNT)
        wrong_qs = result.get("wrong_qs", [])

        st.markdown("### Hiring Manager Interview")
        st.caption(
            f"You scored {score}/{total}. The hiring manager has reviewed your performance "
            "and will now probe your weakest areas."
        )

        # Generate interview questions if not yet done
        if not st.session_state.get("bb_interview_qs"):
            with st.spinner("Hiring manager is reviewing your answers..."):
                qs = _call_hiring_manager(exam, score, wrong_qs)
            if qs:
                st.session_state["bb_interview_qs"] = qs
            else:
                # Fallback questions
                st.session_state["bb_interview_qs"] = [
                    f"Explain a real-world scenario where {exam} concepts prevented a security incident.",
                    f"Walk me through how you would troubleshoot a {wrong_qs[0]['domain'] if wrong_qs else exam} issue step by step.",
                    f"What distinguishes a senior {exam}-certified engineer from a mid-level one in your view?",
                ]

        interview_qs: list[str] = st.session_state["bb_interview_qs"]
        responses: dict = st.session_state.get("bb_responses", {})

        with st.form("bb_interview_form"):
            st.markdown("**Answer all 3 questions below. Be thorough and technical.**")
            for i, q in enumerate(interview_qs):
                st.markdown(f"**Q{i+1}:** {q}")
                responses[i] = st.text_area(
                    f"Your answer to Q{i+1}",
                    value=responses.get(i, ""),
                    key=f"bb_resp_{i}",
                    height=120,
                    label_visibility="collapsed",
                )
            graded = st.form_submit_button(
                "Submit Responses for Grading", type="primary", use_container_width=True
            )

        if graded:
            st.session_state["bb_responses"] = responses
            st.session_state["bb_phase"] = "graded"
            st.rerun()
        return

    # ── Graded phase ──────────────────────────────────────────────────────────
    if phase == "graded":
        result = st.session_state.get("bb_result", {})
        score = result.get("score", 0)
        interview_qs = st.session_state.get("bb_interview_qs", [])
        responses = st.session_state.get("bb_responses", {})

        if not st.session_state.get("bb_grade"):
            with st.spinner("Hiring manager is evaluating your responses..."):
                grade = _call_grade_responses(exam, interview_qs, responses)
            if not grade:
                grade = {
                    "score": 5,
                    "technical_accuracy": "Unable to grade responses at this time — API unavailable.",
                    "communication_clarity": "Please check that ANTHROPIC_API_KEY is set.",
                    "hiring_recommendation": "Maybe",
                    "feedback": "Resubmit when the API connection is restored.",
                }
            st.session_state["bb_grade"] = grade

        grade = st.session_state["bb_grade"]
        hiring_rec = grade.get("hiring_recommendation", "Maybe")
        interview_score = grade.get("score", 5)

        # Award XP and badges
        xp_key = f"bb_xp_awarded_{st.session_state.get('bb_ends_at', '')}"
        if not st.session_state.get(xp_key):
            xp, new_badges = _award_battle_xp(score, hiring_rec)
            save_boss_battle(exam, score, hiring_rec)
            st.session_state[xp_key] = True
            st.session_state["bb_new_badges"] = new_badges
            st.session_state["bb_xp_earned"] = xp

        # Display results
        rec_colors = {
            "Strong Yes": "success",
            "Yes": "success",
            "Maybe": "warning",
            "No": "error",
        }
        rec_display = rec_colors.get(hiring_rec, "info")

        st.markdown("### Hiring Manager Verdict")
        if hiring_rec == "Strong Yes":
            st.success(f"Hiring Recommendation: **{hiring_rec}**")
            st.balloons()
        elif hiring_rec == "Yes":
            st.success(f"Hiring Recommendation: **{hiring_rec}**")
        elif hiring_rec == "Maybe":
            st.warning(f"Hiring Recommendation: **{hiring_rec}**")
        else:
            st.error(f"Hiring Recommendation: **{hiring_rec}**")

        col1, col2 = st.columns(2)
        col1.metric("Battle Score", f"{score}/{_BATTLE_QUESTION_COUNT}")
        col2.metric("Interview Score", f"{interview_score}/10")

        st.markdown(f"**Technical Accuracy:** {grade.get('technical_accuracy', '')}")
        st.markdown(f"**Communication Clarity:** {grade.get('communication_clarity', '')}")
        st.markdown(f"**Feedback:** {grade.get('feedback', '')}")

        xp_earned = st.session_state.get("bb_xp_earned", 0)
        if xp_earned:
            st.info(f"+{xp_earned:,} XP earned!")

        for b in st.session_state.get("bb_new_badges", []):
            st.success(f"Badge unlocked: **{b}**!")

        # Show full question review with explanations
        with st.expander("Full Battle Review with Explanations"):
            questions = st.session_state.get("bb_questions", [])
            answers = st.session_state.get("bb_answers", {})
            for i, q in enumerate(questions):
                sel = answers.get(q["id"])
                is_correct = sel == q["correct_answer"]
                icon = "✅" if is_correct else "❌"
                with st.expander(f"{icon} Q{i+1}: {q['topic']}", expanded=not is_correct):
                    st.markdown(q["stem"])
                    st.markdown(f"**Your answer:** {sel or '*(no answer)*'}")
                    if not is_correct:
                        st.markdown(f"**Correct:** {q['correct_answer']}")
                    st.caption(q["explanation"])

        if st.button("Start New Boss Battle", key="bb_reset"):
            for key in [
                "bb_phase", "bb_exam", "bb_questions", "bb_current",
                "bb_answers", "bb_ends_at", "bb_result", "bb_interview_qs",
                "bb_responses", "bb_grade", "bb_new_badges", "bb_xp_earned",
            ]:
                st.session_state.pop(key, None)
            st.rerun()


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]
    selected_count = ctx["selected_count"]
    timed_mode = ctx["timed_mode"]
    minutes = ctx["minutes"]
    current_readiness = ctx["current_readiness"]

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

    # Debate Mode section
    _render_debate_mode(selected_exam)

    # Boss Battle section
    _render_boss_battle(selected_exam, current_readiness)
