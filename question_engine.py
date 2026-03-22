from __future__ import annotations

import random
import uuid
from collections import defaultdict

from exams import get_question_pool


QUESTION_STEMS = [
    "Which statement is correct about {concept}?",
    "In {exam}, what best describes {concept}?",
    "Choose the best answer for {concept}.",
    "A student is reviewing {domain}. Which statement is accurate about {concept}?",
]

SCENARIO_PREFIXES = {
    "practice": [
        "Quick drill:",
        "Concept check:",
        "Lock this in:",
        "You need the cleanest definition here:",
    ],
    "exam": [
        "Exam-style prompt:",
        "Under time pressure, identify the best answer:",
        "On the real exam, this is the kind of wording to expect:",
        "Pick the most defensible answer:",
    ],
}


def _select_fact_sequence(pool: list[dict], question_count: int, rng: random.Random) -> list[dict]:
    by_domain = defaultdict(list)
    for fact in pool:
        by_domain[fact["domain"]].append(fact)

    for facts in by_domain.values():
        rng.shuffle(facts)

    domain_order = list(by_domain.keys())
    rng.shuffle(domain_order)
    usage_by_topic = defaultdict(int)
    sequence = []
    cursor = 0

    while len(sequence) < question_count:
        domain = domain_order[cursor % len(domain_order)]
        facts = by_domain[domain]
        min_usage = min(usage_by_topic[fact["concept"]] for fact in facts)
        candidates = [fact for fact in facts if usage_by_topic[fact["concept"]] == min_usage]

        if sequence:
            last_topic = sequence[-1]["concept"]
            filtered = [fact for fact in candidates if fact["concept"] != last_topic]
            if filtered:
                candidates = filtered

        chosen = rng.choice(candidates)
        usage_by_topic[chosen["concept"]] += 1
        sequence.append(chosen)
        cursor += 1

    return sequence


def _build_stem(fact: dict, exam: str, mode: str, rng: random.Random) -> str:
    prefix = rng.choice(SCENARIO_PREFIXES["exam" if mode == "exam" else "practice"])
    stem = rng.choice(QUESTION_STEMS).format(concept=fact["concept"], exam=exam, domain=fact["domain"])
    return f"{prefix} {stem}"


def generate_quiz(exam: str, domains: list[str], question_count: int, mode: str) -> list[dict]:
    pool = get_question_pool(exam, domains)
    if not pool:
        return []

    rng = random.Random()
    sequence = _select_fact_sequence(pool, question_count, rng)
    questions = []
    for fact in sequence:
        options = [fact["correct"], *rng.sample(fact["distractors"], k=3)]
        rng.shuffle(options)
        stem = _build_stem(fact, exam, mode, rng)
        questions.append(
            {
                "id": str(uuid.uuid4()),
                "exam": exam,
                "domain": fact["domain"],
                "topic": fact["concept"],
                "stem": stem,
                "options": options,
                "correct_answer": fact["correct"],
                "explanation": fact["explanation"],
                "mode": mode,
            }
        )
    return questions


def award_quiz_xp(
    evaluated: dict,
    score_pct: float,
    elapsed_seconds: int,
    question_count: int,
    hour: int | None = None,
) -> dict:
    """Award XP and badges after a submitted quiz. Returns a summary dict for display."""
    from storage import add_xp, award_badge, get_badges  # lazy import avoids circular dependency

    xp_earned = 0
    badges_earned = []

    correct = evaluated["correct_count"]
    wrong = question_count - correct

    if correct > 0:
        add_xp(correct * 10, f"Correct answers ({correct}×)")
        xp_earned += correct * 10
    if wrong > 0:
        add_xp(wrong * 2, f"Attempted ({wrong} incorrect)")
        xp_earned += wrong * 2

    add_xp(50, "Quiz completed")
    xp_earned += 50

    if score_pct >= 90:
        add_xp(150, "Score above 90%")
        xp_earned += 150
    elif score_pct >= 80:
        add_xp(75, "Score above 80%")
        xp_earned += 75

    existing = {b["badge_id"] for b in get_badges()}

    if "first_steps" not in existing:
        add_xp(100, "First quiz bonus")
        xp_earned += 100
        if award_badge("first_steps", "First Steps", "Completed your first quiz"):
            badges_earned.append("First Steps")

    if score_pct == 100:
        if award_badge("perfect_score", "Perfect Score", "Scored 100% on a quiz"):
            badges_earned.append("Perfect Score")

    if question_count == 25 and elapsed_seconds < 300:
        if award_badge("speed_demon", "Speed Demon", "Completed a 25-question quiz in under 5 minutes"):
            badges_earned.append("Speed Demon")

    for ds in evaluated.get("domain_breakdown", []):
        if ds.get("accuracy_pct", 0) >= 90 and ds.get("total", 0) >= 3:
            if award_badge("domain_dominator", "Domain Dominator", "Achieved 90%+ accuracy in a domain"):
                badges_earned.append("Domain Dominator")
            break

    if hour is not None and 0 <= hour < 1:
        if award_badge("night_owl", "Night Owl", "Completed a quiz after midnight"):
            badges_earned.append("Night Owl")

    if hour is not None and hour < 7:
        if award_badge("early_bird", "Early Bird", "Completed a quiz before 7am"):
            badges_earned.append("Early Bird")

    return {"xp_earned": xp_earned, "badges_earned": badges_earned}


def get_ai_tutor_explanation(
    question: dict,
    selected_answer: str | None,
    correct_answer: str,
    domain: str,
    topic: str,
    weak_topics: list[str] | None = None,
) -> dict | None:
    """Call Claude to generate a step-by-step explanation for a wrong answer.

    Returns a dict with keys: step1, step2, step3, memory_tip, follow_up.
    Returns None on any error so the caller can show a fallback message.
    """
    try:
        import json as _json

        import anthropic

        client = anthropic.Anthropic()

        context_parts = [
            f"Domain: {domain}",
            f"Topic: {topic}",
            f"Question: {question['stem']}",
            f"Correct answer: {correct_answer}",
            f"Student selected: {selected_answer or 'No answer selected'}",
        ]
        if weak_topics:
            context_parts.append(f"Student's known weak topics: {', '.join(weak_topics[:5])}")
        context = "\n".join(context_parts)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=(
                "You are an expert IT certification tutor. "
                "Respond ONLY with a JSON object with exactly these keys:\n"
                "- step1: What the correct answer means and why it is right (2-3 sentences)\n"
                "- step2: Why the wrong answer was tempting but incorrect; if no answer was selected, explain the most common misconception (1-2 sentences)\n"
                "- step3: How to distinguish this concept from similar ones going forward (1-2 sentences)\n"
                "- memory_tip: A memorable mnemonic, acronym, or mental model (1 sentence)\n"
                "- follow_up: A follow-up question that tests deeper understanding (1 sentence ending with ?)\n"
                "Output only valid JSON with no markdown fences or extra text."
            ),
            messages=[{"role": "user", "content": context}],
        )

        text = next((b.text for b in response.content if b.type == "text"), "")
        return _json.loads(text)
    except Exception:
        return None


def evaluate_submission(questions: list[dict], answers: dict[str, str | None]) -> dict:
    review = []
    domain_stats = {}
    topic_results = []
    correct_count = 0

    for question in questions:
        selected = answers.get(question["id"])
        is_correct = selected == question["correct_answer"]
        correct_count += int(is_correct)
        review.append(
            {
                "id": question["id"],
                "stem": question["stem"],
                "domain": question["domain"],
                "topic": question["topic"],
                "selected_answer": selected,
                "correct_answer": question["correct_answer"],
                "explanation": question["explanation"],
                "is_correct": is_correct,
            }
        )
        topic_results.append(
            {
                "domain": question["domain"],
                "topic": question["topic"],
                "correct": is_correct,
            }
        )
        bucket = domain_stats.setdefault(question["domain"], {"domain": question["domain"], "correct": 0, "total": 0})
        bucket["correct"] += int(is_correct)
        bucket["total"] += 1

    domain_breakdown = []
    for item in domain_stats.values():
        domain_breakdown.append(
            {
                "domain": item["domain"],
                "correct": item["correct"],
                "total": item["total"],
                "accuracy_pct": round((item["correct"] / item["total"]) * 100, 1) if item["total"] else 0.0,
            }
        )

    score_pct = round((correct_count / len(questions)) * 100, 1) if questions else 0.0
    return {
        "review": review,
        "correct_count": correct_count,
        "score_pct": score_pct,
        "domain_breakdown": domain_breakdown,
        "topic_results": topic_results,
    }
