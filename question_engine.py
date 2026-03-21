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
