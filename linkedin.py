from __future__ import annotations

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRIGGER_LABELS: dict[str, str] = {
    "lab_completed": "Lab Completed",
    "quiz_milestone": "Quiz Score 85%+",
    "readiness_jump": "Readiness Jump +10 pts",
    "resume_generated": "Resume Generated",
    "cert_mastered": "Cert Readiness Hit 80%",
}

# Monday=0 … Sunday=6. Best days: Tue=1, Wed=2, Thu=3
_PEAK_DAYS: frozenset[int] = frozenset({1, 2, 3})

# (start_hour, start_min, end_hour, end_min) in 24-h local time
_PEAK_WINDOWS: list[tuple[int, int, int, int]] = [
    (7, 30, 8, 30),
    (12, 0, 13, 0),
    (17, 0, 18, 0),
]


# ---------------------------------------------------------------------------
# Peak time helper
# ---------------------------------------------------------------------------

def _fmt_time(dt: datetime) -> str:
    hour = dt.hour % 12 or 12
    minute = dt.strftime("%M")
    am_pm = "AM" if dt.hour < 12 else "PM"
    return f"{hour}:{minute} {am_pm}"


def get_next_peak_time() -> dict:
    """Return metadata about the next ideal LinkedIn posting window.

    Keys returned:
        day        — weekday name, e.g. "Tuesday"
        date       — e.g. "Mar 25"
        time_range — e.g. "7:30 AM – 8:30 AM"
        datetime   — datetime object of window start
        is_now     — True when we're currently inside a peak window
        days_until — 0 = today, 1 = tomorrow, etc.
        label      — "Right now!" / "Today" / "Tomorrow" / weekday name
    """
    now = datetime.now()
    for days_ahead in range(8):
        check = now + timedelta(days=days_ahead)
        if check.weekday() not in _PEAK_DAYS:
            continue
        for sh, sm, eh, em in _PEAK_WINDOWS:
            w_start = check.replace(hour=sh, minute=sm, second=0, microsecond=0)
            w_end = check.replace(hour=eh, minute=em, second=0, microsecond=0)
            if days_ahead == 0 and w_end <= now:
                continue  # window already passed
            is_now = days_ahead == 0 and w_start <= now < w_end
            if days_ahead == 0 and is_now:
                label = "Right now!"
            elif days_ahead == 0:
                label = "Today"
            elif days_ahead == 1:
                label = "Tomorrow"
            else:
                label = w_start.strftime("%A")
            return {
                "day": w_start.strftime("%A"),
                "date": w_start.strftime("%b %d"),
                "time_range": f"{_fmt_time(w_start)} – {_fmt_time(w_end)}",
                "datetime": w_start,
                "is_now": is_now,
                "days_until": days_ahead,
                "label": label,
            }
    # Fallback — should never be reached
    fallback = now + timedelta(days=1)
    return {
        "day": "Tuesday",
        "date": fallback.strftime("%b %d"),
        "time_range": "7:30 AM – 8:30 AM",
        "datetime": fallback,
        "is_now": False,
        "days_until": 1,
        "label": "Tomorrow",
    }


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(trigger: str, user_data: dict) -> str:
    user_name = user_data.get("user_name", "I")
    cert = user_data.get("cert", "my certification")

    if trigger == "lab_completed":
        lab_title = user_data.get("lab_title", "a hands-on lab")
        grade_score = user_data.get("grade_score", 8)
        bullets = user_data.get("bullets", [])
        bullets_text = "\n".join(f"- {b}" for b in bullets) if bullets else ""
        achievement = (
            f"Just completed the '{lab_title}' hands-on home lab for {cert} "
            f"and received an AI grade of {grade_score}/10.\n"
            f"Lab resume bullets unlocked:\n{bullets_text}"
        )

    elif trigger == "quiz_milestone":
        score_pct = user_data.get("score_pct", 85)
        question_count = user_data.get("question_count", 25)
        exam = user_data.get("exam", cert)
        achievement = (
            f"Just scored {score_pct:.0f}% on a {question_count}-question {exam} practice quiz. "
            "This is a strong performance that shows the study system is working."
        )

    elif trigger == "readiness_jump":
        before = user_data.get("readiness_before", 60)
        after = user_data.get("readiness_after", 72)
        exam = user_data.get("exam", cert)
        jump = after - before
        achievement = (
            f"Readiness score for {exam} jumped {jump:.0f} points — "
            f"from {before:.0f} to {after:.0f} — in a single study session. "
            "The analytics are showing real momentum."
        )

    elif trigger == "resume_generated":
        labs_count = user_data.get("labs_count", 0)
        certs_count = user_data.get("certs_count", 0)
        job_title = user_data.get("job_title", "a tech role")
        achievement = (
            f"Just built an ATS-optimized resume for {job_title} using "
            f"{labs_count} completed hands-on lab "
            f"{'project' if labs_count == 1 else 'projects'} and "
            f"{certs_count} certification {'track' if certs_count == 1 else 'tracks'}. "
            "The labs turned into real project experience on paper."
        )

    elif trigger == "cert_mastered":
        readiness = user_data.get("readiness", 80)
        achievement = (
            f"Readiness for {cert} just crossed {readiness:.0f}%. "
            "That threshold in the practice system signals exam-level confidence."
        )

    else:
        achievement = f"Making great progress toward {cert}."

    return f"""Write a LinkedIn post for someone sharing this achievement:

Person: {user_name}
Cert being studied: {cert}
Achievement: {achievement}

STRICT REQUIREMENTS — follow every one:
- Total length: under 280 words
- Line 1 (hook): A single punchy sentence that stops the scroll. No clichés like "Excited to share" or "Thrilled to announce".
- Then a blank line
- Then 3–4 bullet points starting with ▸ covering what was learned or accomplished
- Then a blank line
- Then 1–2 sentences of personal insight or lesson learned
- Then a blank line
- Then exactly 1 sentence mentioning they're using NetSecure StudyOS to track cert progress
- Then a blank line
- Then exactly 5 relevant hashtags separated by spaces
- Emojis: use 3–5 total, placed naturally — not on every line

Output ONLY the post text. No quotes, no preamble, no markdown fences.
"""


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------

def generate_linkedin_post(trigger: str, user_data: dict) -> str | None:
    """Call Claude claude-sonnet-4-6 to generate a LinkedIn post.

    Args:
        trigger:   One of the TRIGGER_LABELS keys.
        user_data: Dict with context fields relevant to the trigger type.

    Returns:
        Post text string (≤ 280 words) or None on any error.
    """
    try:
        import anthropic

        client = anthropic.Anthropic()
        prompt = _build_prompt(trigger, user_data)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=(
                "You are an expert LinkedIn content writer who helps IT professionals "
                "authentically share their certification study journey. Your posts are "
                "specific, conversational, professional, and never cringe. First person. "
                "No corporate jargon."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        return text.strip() or None
    except Exception:
        return None
