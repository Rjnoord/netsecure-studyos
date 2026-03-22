from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import pstdev

import pandas as pd

from exams import EXAM_DOMAINS


def _filter_exam(exam: str, results: list[dict]) -> list[dict]:
    return sorted(
        [result for result in results if result.get("exam") == exam],
        key=lambda item: item.get("submitted_at", ""),
    )


def _profile_target_context(exam: str, profile: dict | None) -> tuple[float, float, dict[str, int]]:
    if not profile:
        return 0.0, 0.0, {}

    target_bonus = 4.0 if profile.get("target_exam") == exam else 0.0
    weekly_hours = float(profile.get("weekly_study_hours", 0) or 0)
    study_capacity_bonus = min(weekly_hours * 0.6, 6.0)
    self_ratings = profile.get("domain_self_ratings", {}).get(exam, {})
    return target_bonus, study_capacity_bonus, self_ratings


def _days_until_target(profile: dict | None, exam: str) -> int | None:
    if not profile or profile.get("target_exam") != exam or not profile.get("target_date"):
        return None
    try:
        target_date = datetime.fromisoformat(profile["target_date"]).date()
        return (target_date - datetime.now().date()).days
    except ValueError:
        return None


def _topic_frame(exam: str, results: list[dict]) -> pd.DataFrame:
    rows = []
    scoped = _filter_exam(exam, results)
    total_attempts = max(1, len(scoped))

    for attempt_index, result in enumerate(scoped, start=1):
        submitted = datetime.fromisoformat(result["submitted_at"])
        recency_ratio = attempt_index / total_attempts
        recency_weight = 0.8 + (recency_ratio**2) * 2.2
        for topic_result in result.get("topic_results", []):
            rows.append(
                {
                    "domain": topic_result["domain"],
                    "topic": topic_result["topic"],
                    "correct": int(topic_result["correct"]),
                    "miss": int(not topic_result["correct"]),
                    "recency_weight": recency_weight,
                    "submitted_at": submitted,
                }
            )
    return pd.DataFrame(rows)


def _recent_topic_streaks(df: pd.DataFrame) -> dict[tuple[str, str], int]:
    streaks: dict[tuple[str, str], int] = {}
    if df.empty:
        return streaks

    ordered = df.sort_values("submitted_at")
    for (domain, topic), group in ordered.groupby(["domain", "topic"]):
        streak = 0
        for is_correct in reversed(group["correct"].tolist()):
            if not is_correct:
                break
            streak += 1
        streaks[(domain, topic)] = streak
    return streaks


def _domain_confidence_frame(exam: str, results: list[dict]) -> pd.DataFrame:
    df = _topic_frame(exam, results)
    if df.empty:
        return pd.DataFrame()

    grouped = (
        df.assign(
            weighted_correct=df["correct"] * df["recency_weight"],
            weighted_total=df["recency_weight"],
        )
        .groupby("domain", as_index=False)
        .agg(
            attempts=("domain", "size"),
            weighted_correct=("weighted_correct", "sum"),
            weighted_total=("weighted_total", "sum"),
        )
    )
    grouped["confidence_pct"] = (grouped["weighted_correct"] / grouped["weighted_total"] * 100).round(1)
    return grouped.sort_values("confidence_pct", ascending=False)


def _topic_summary_frame(exam: str, results: list[dict]) -> pd.DataFrame:
    df = _topic_frame(exam, results)
    if df.empty:
        return pd.DataFrame()

    streaks = _recent_topic_streaks(df)
    grouped = (
        df.assign(
            weighted_correct=df["correct"] * df["recency_weight"],
            weighted_miss=df["miss"] * df["recency_weight"] * 1.35,
        )
        .groupby(["domain", "topic"], as_index=False)
        .agg(
            attempts=("topic", "size"),
            weighted_correct=("weighted_correct", "sum"),
            weighted_miss=("weighted_miss", "sum"),
            total_weight=("recency_weight", "sum"),
            last_seen=("submitted_at", "max"),
        )
    )
    grouped["weighted_accuracy"] = grouped["weighted_correct"] / grouped["total_weight"] * 100
    grouped["correct_streak"] = grouped.apply(lambda row: streaks.get((row["domain"], row["topic"]), 0), axis=1)
    grouped["miss_pressure"] = grouped["weighted_miss"]
    return grouped


def calculate_readiness(exam: str, results: list[dict], profile: dict | None = None) -> float:
    scoped = _filter_exam(exam, results)
    target_bonus, study_capacity_bonus, self_ratings = _profile_target_context(exam, profile)
    if not scoped:
        self_rating_avg = ((sum(self_ratings.values()) / len(self_ratings)) * 20) if self_ratings else 58.0
        baseline = 30.0 + (self_rating_avg * 0.10) + target_bonus + study_capacity_bonus
        return round(min(55.0, max(28.0, baseline)), 1)

    recent = scoped[-10:]
    scores = [float(item["score_pct"]) for item in recent]
    ema = scores[0]
    for score in scores[1:]:
        ema = (score * 0.35) + (ema * 0.65)

    recent_average = sum(scores) / len(scores)
    total_questions = sum(int(item.get("question_count", 0)) for item in scoped)
    volume_factor = min(total_questions / 220, 1.0)
    score_variation = pstdev(scores) if len(scores) > 1 else 6.0
    stability = max(58.0, 100 - (score_variation * 2.2))

    domain_confidence = _domain_confidence_frame(exam, results)
    domain_component = (
        float(domain_confidence["confidence_pct"].mean()) if not domain_confidence.empty else recent_average
    )
    self_rating_component = ((sum(self_ratings.values()) / len(self_ratings)) * 20) if self_ratings else domain_component

    practiced_domains = {
        item["domain"] for result in scoped for item in result.get("domain_breakdown", []) if item.get("total")
    }
    coverage = len(practiced_domains) / max(1, len(EXAM_DOMAINS[exam]))
    days_left = _days_until_target(profile, exam)
    urgency_modifier = 0.0
    if days_left is not None:
        if days_left <= 14:
            urgency_modifier = -3.5
        elif days_left <= 30:
            urgency_modifier = -1.5
        elif days_left >= 75:
            urgency_modifier = 1.5

    readiness = (
        (ema * 0.42)
        + (recent_average * 0.18)
        + (domain_component * 0.16)
        + (self_rating_component * 0.06)
        + (stability * 0.10)
        + (coverage * 100 * 0.08)
        + (volume_factor * 100 * 0.06)
        + target_bonus
        + study_capacity_bonus
        + urgency_modifier
    )
    return round(min(99.0, max(32.0, readiness)), 1)


def weakest_topics(exam: str, results: list[dict], limit: int = 5) -> list[dict]:
    grouped = _topic_summary_frame(exam, results)
    if grouped.empty:
        return []
    grouped["priority_score"] = (
        grouped["weighted_miss"] * 1.8
        + ((100 - grouped["weighted_accuracy"]) * 0.10)
        - (grouped["correct_streak"] * 2.6)
    )
    grouped = grouped.drop(columns=["weighted_correct", "weighted_miss", "total_weight"])
    grouped = grouped.sort_values(["priority_score", "weighted_accuracy"], ascending=[False, True])
    grouped["weighted_accuracy"] = grouped["weighted_accuracy"].round(1)
    grouped["priority_score"] = grouped["priority_score"].round(2)
    return grouped.head(limit).to_dict(orient="records")


def strongest_topics(exam: str, results: list[dict], limit: int = 5) -> list[dict]:
    df = _topic_frame(exam, results)
    if df.empty:
        return []

    streaks = _recent_topic_streaks(df)
    df = df.assign(weighted_correct=df["correct"] * df["recency_weight"])
    grouped = (
        df.groupby(["domain", "topic"], as_index=False)
        .agg(
            attempts=("topic", "size"),
            weighted_correct=("weighted_correct", "sum"),
            total_weight=("recency_weight", "sum"),
        )
    )
    grouped["weighted_accuracy"] = grouped["weighted_correct"] / grouped["total_weight"] * 100
    grouped["correct_streak"] = grouped.apply(lambda row: streaks.get((row["domain"], row["topic"]), 0), axis=1)
    grouped["mastery_score"] = grouped["weighted_accuracy"] + (grouped["correct_streak"] * 4)
    grouped = grouped.drop(columns=["weighted_correct", "total_weight"])
    grouped = grouped.sort_values(["mastery_score", "attempts"], ascending=[False, False])
    grouped["weighted_accuracy"] = grouped["weighted_accuracy"].round(1)
    grouped["mastery_score"] = grouped["mastery_score"].round(2)
    return grouped.head(limit).to_dict(orient="records")


def topic_history_frame(exam: str, results: list[dict]) -> pd.DataFrame:
    scoped = _filter_exam(exam, results)
    rows = []
    streaks: dict[tuple[str, str], int] = defaultdict(int)
    for result in scoped:
        submitted_at = datetime.fromisoformat(result["submitted_at"])
        for item in result.get("topic_results", []):
            key = (item["domain"], item["topic"])
            if item["correct"]:
                streaks[key] += 1
            else:
                streaks[key] = 0
            rows.append(
                {
                    "submitted_at": submitted_at,
                    "domain": item["domain"],
                    "topic": item["topic"],
                    "result": "Correct" if item["correct"] else "Missed",
                    "streak_after_attempt": streaks[key],
                }
            )
    if not rows:
        return pd.DataFrame(columns=["submitted_at", "domain", "topic", "result", "streak_after_attempt"])
    return pd.DataFrame(rows)


def improved_topics(exam: str, results: list[dict], limit: int = 5) -> list[dict]:
    history = topic_history_frame(exam, results)
    if history.empty:
        return []

    rows = []
    for (domain, topic), group in history.groupby(["domain", "topic"]):
        if len(group) < 2:
            continue
        first_chunk = group.head(min(3, len(group)))
        last_chunk = group.tail(min(3, len(group)))
        first_accuracy = (first_chunk["result"].eq("Correct").mean() * 100)
        last_accuracy = (last_chunk["result"].eq("Correct").mean() * 100)
        improvement = round(last_accuracy - first_accuracy, 1)
        if improvement > 0:
            rows.append(
                {
                    "domain": domain,
                    "topic": topic,
                    "start_accuracy": round(first_accuracy, 1),
                    "current_accuracy": round(last_accuracy, 1),
                    "improvement": improvement,
                }
            )
    rows.sort(key=lambda item: item["improvement"], reverse=True)
    return rows[:limit]


def review_queue(exam: str, results: list[dict]) -> pd.DataFrame:
    grouped = _topic_summary_frame(exam, results)
    if grouped.empty:
        return pd.DataFrame(
            columns=[
                "domain",
                "topic",
                "review_status",
                "weighted_accuracy",
                "correct_streak",
                "recommended_gap_days",
                "last_seen",
            ]
        )

    grouped["priority_score"] = (
        grouped["weighted_miss"] * 1.7
        + ((100 - grouped["weighted_accuracy"]) * 0.12)
        - (grouped["correct_streak"] * 3.1)
    )
    grouped["recommended_gap_days"] = grouped["correct_streak"].apply(
        lambda streak: 1 if streak <= 0 else 2 if streak == 1 else 4 if streak == 2 else 7
    )
    grouped["review_status"] = grouped["priority_score"].apply(
        lambda score: "Review now" if score >= 9 else "Review soon" if score >= 4 else "Maintain"
    )
    status_rank = {"Review now": 0, "Review soon": 1, "Maintain": 2}
    grouped["status_rank"] = grouped["review_status"].map(status_rank).fillna(3)
    grouped["weighted_accuracy"] = grouped["weighted_accuracy"].round(1)
    grouped["last_seen"] = grouped["last_seen"].dt.strftime("%b %d, %Y")
    return grouped[
        [
            "domain",
            "topic",
            "review_status",
            "weighted_accuracy",
            "correct_streak",
            "recommended_gap_days",
            "last_seen",
            "status_rank",
        ]
    ].sort_values(["status_rank", "weighted_accuracy"], ascending=[True, True]).drop(columns=["status_rank"])


def performance_over_time(exam: str, results: list[dict]) -> pd.DataFrame:
    scoped = _filter_exam(exam, results)
    if not scoped:
        return pd.DataFrame()

    frame = pd.DataFrame(
        [
            {
                "submitted_at": datetime.fromisoformat(item["submitted_at"]),
                "score_pct": item["score_pct"],
                "mode": item["mode"],
                "question_count": item.get("question_count", 0),
            }
            for item in scoped
        ]
    ).sort_values("submitted_at")
    frame["rolling_score"] = frame["score_pct"].ewm(alpha=0.35, adjust=False).mean().round(1)
    return frame


def domain_breakdown(exam: str, results: list[dict]) -> pd.DataFrame:
    scoped = _filter_exam(exam, results)
    if not scoped:
        return pd.DataFrame()

    rows = []
    total_attempts = max(1, len(scoped))
    for index, result in enumerate(scoped, start=1):
        recency_weight = 0.9 + ((index / total_attempts) ** 2) * 1.8
        for item in result.get("domain_breakdown", []):
            rows.append(
                {
                    "domain": item["domain"],
                    "correct": item["correct"],
                    "total": item["total"],
                    "weighted_correct": item["correct"] * recency_weight,
                    "weighted_total": item["total"] * recency_weight,
                }
            )
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    grouped = df.groupby("domain", as_index=False).agg(
        correct=("correct", "sum"),
        total=("total", "sum"),
        weighted_correct=("weighted_correct", "sum"),
        weighted_total=("weighted_total", "sum"),
    )
    grouped["accuracy_pct"] = (grouped["correct"] / grouped["total"] * 100).round(1)
    grouped["confidence_pct"] = (grouped["weighted_correct"] / grouped["weighted_total"] * 100).round(1)
    return grouped.sort_values("confidence_pct")


def confidence_by_domain(exam: str, results: list[dict]) -> pd.DataFrame:
    scoped = _filter_exam(exam, results)
    if not scoped:
        return pd.DataFrame(
            [
                {
                    "domain": domain,
                    "confidence_pct": 0.0,
                    "recent_avg": 0.0,
                    "attempts": 0,
                    "signal": "No data yet",
                }
                for domain in EXAM_DOMAINS[exam]
            ]
        )

    rows = []
    recent_window = scoped[-4:]
    for domain in EXAM_DOMAINS[exam]:
        weighted_correct = 0.0
        weighted_total = 0.0
        recent_scores = []
        attempts = 0
        for index, result in enumerate(scoped, start=1):
            for item in result.get("domain_breakdown", []):
                if item["domain"] != domain:
                    continue
                recency_weight = 0.85 + ((index / len(scoped)) ** 2) * 2.1
                weighted_correct += item["correct"] * recency_weight
                weighted_total += item["total"] * recency_weight
                attempts += 1
        for result in recent_window:
            for item in result.get("domain_breakdown", []):
                if item["domain"] == domain and item["total"]:
                    recent_scores.append(item["accuracy_pct"])
        confidence_pct = round((weighted_correct / weighted_total) * 100, 1) if weighted_total else 0.0
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0.0
        if confidence_pct >= 82:
            signal = "Ready to maintain"
        elif confidence_pct >= 68:
            signal = "Stable but worth revisiting"
        elif attempts:
            signal = "Needs focused reps"
        else:
            signal = "No data yet"
        rows.append(
            {
                "domain": domain,
                "confidence_pct": confidence_pct,
                "recent_avg": round(recent_avg, 1),
                "attempts": attempts,
                "signal": signal,
            }
        )
    return pd.DataFrame(rows).sort_values("confidence_pct", ascending=False)


def recommended_next_topic(exam: str, results: list[dict], profile: dict | None = None) -> dict:
    weak = weakest_topics(exam, results, limit=1)
    self_ratings = (profile or {}).get("domain_self_ratings", {}).get(exam, {})
    if self_ratings:
        lowest_domain = min(self_ratings, key=self_ratings.get)
        lowest_domain_score = self_ratings[lowest_domain]
    else:
        lowest_domain = None
        lowest_domain_score = None

    if weak:
        item = weak[0]
        reason = (
            f"Recent misses are still concentrated here, and the current weighted accuracy is "
            f"{item['weighted_accuracy']:.1f}%."
        )
        if lowest_domain and item["domain"] == lowest_domain:
            reason += f" You also rated {lowest_domain} lower in onboarding, so it should stay near the top of the queue."
        if item["correct_streak"] >= 2:
            reason = (
                f"This was weak recently, but the {item['correct_streak']}-question correct streak is lowering its urgency."
            )
        return {
            "topic": item["topic"],
            "domain": item["domain"],
            "reason": reason,
            "confidence_gap": round(100 - item["weighted_accuracy"], 1),
        }

    first_domain = lowest_domain or EXAM_DOMAINS[exam][0]
    return {
        "topic": first_domain,
        "domain": first_domain,
        "reason": (
            f"No saved quiz history yet, so start with {first_domain}. "
            + (
                f"You rated this domain {lowest_domain_score}/5 during onboarding, making it the best place to build confidence first."
                if lowest_domain
                else "Build a baseline in a high-yield core domain first."
            )
        ),
        "confidence_gap": 0.0,
    }


def recommend_study_next(exam: str, results: list[dict], profile: dict | None = None) -> list[str]:
    weak = weakest_topics(exam, results, limit=3)
    self_ratings = (profile or {}).get("domain_self_ratings", {}).get(exam, {})
    if not weak:
        lowest = min(self_ratings, key=self_ratings.get) if self_ratings else EXAM_DOMAINS[exam][0]
        return [
            f"Start with {lowest} to match your onboarding confidence gaps.",
            "Take a 10-question practice quiz to establish a baseline.",
            "Use the cheat sheets before your next scored attempt.",
        ]

    lines = []
    for item in weak:
        line = (
            f"{item['topic']} in {item['domain']} is costing points. "
            f"Weighted accuracy is {item['weighted_accuracy']:.1f}%."
        )
        if item["correct_streak"] >= 2:
            line += f" The {item['correct_streak']}-question correct streak is helping, so keep it warm instead of overdrilling."
        lines.append(line)
    return lines


def build_study_plan(exam: str, hours_available: int, results: list[dict], profile: dict | None = None) -> dict:
    weak = weakest_topics(exam, results, limit=4)
    total_minutes = hours_available * 60
    self_ratings = (profile or {}).get("domain_self_ratings", {}).get(exam, {})

    if weak:
        total_priority = sum(max(item["priority_score"], 1) for item in weak)
        topics = []
        for index, item in enumerate(weak, start=1):
            share = max(item["priority_score"], 1) / total_priority
            confidence_penalty = max(0, 4 - int(self_ratings.get(item["domain"], 3))) * 10
            minutes = max(30, round((total_minutes * share + confidence_penalty) / 5) * 5)
            topics.append(
                {
                    "priority": index,
                    "topic": item["topic"],
                    "domain": item["domain"],
                    "estimated_minutes": minutes,
                    "why_it_matters": (
                        f"Recent misses in {item['domain']} still outweigh recovery, so this topic is suppressing readiness."
                        + (
                            f" You also rated this domain {self_ratings.get(item['domain'], 3)}/5 in onboarding."
                            if item["domain"] in self_ratings
                            else ""
                        )
                    ),
                    "focus": (
                        "Review the cheat sheet, explain the concept out loud, then finish with a short practice block."
                    ),
                }
            )
    else:
        seed_domains = sorted(
            EXAM_DOMAINS[exam],
            key=lambda domain: self_ratings.get(domain, 3),
        )[:4]
        minutes_per_topic = max(30, total_minutes // max(1, len(seed_domains)))
        topics = [
            {
                "priority": index + 1,
                "topic": domain,
                "domain": domain,
                "estimated_minutes": minutes_per_topic,
                "why_it_matters": (
                    f"{domain} is a high-yield starting point for {exam}."
                    + (
                        f" You rated it {self_ratings.get(domain, 3)}/5, so it belongs early in the plan."
                        if domain in self_ratings
                        else ""
                    )
                ),
                "focus": "Build baseline familiarity with the domain, then validate it with a short quiz.",
            }
            for index, domain in enumerate(seed_domains)
        ]

    total_focus_minutes = sum(item["estimated_minutes"] for item in topics)
    recovery_minutes = max(20, total_minutes - total_focus_minutes)
    return {
        "topics": topics,
        "recovery_block_minutes": recovery_minutes,
        "closing_step": "Finish the week with one timed attempt and review every miss before ending the session.",
    }


def predict_exam_score(exam: str, results: list[dict], profile: dict | None = None) -> dict:
    scoped = _filter_exam(exam, results)
    readiness = calculate_readiness(exam, results, profile)
    domain_conf = confidence_by_domain(exam, results)
    self_ratings = (profile or {}).get("domain_self_ratings", {}).get(exam, {})
    self_rating_avg = ((sum(self_ratings.values()) / len(self_ratings)) * 20) if self_ratings else readiness

    if not scoped:
        center = round((readiness * 0.58) + (self_rating_avg * 0.12) + 15, 1)
        return {
            "predicted_score": center,
            "range_low": round(max(35.0, center - 10), 1),
            "range_high": round(min(89.0, center + 10), 1),
            "confidence_note": "Low confidence. The model needs recent quiz history to tighten the range.",
            "question_volume": 0,
            "history_count": 0,
        }

    recent = scoped[-6:]
    recent_average = sum(item["score_pct"] for item in recent) / len(recent)
    overall_average = sum(item["score_pct"] for item in scoped) / len(scoped)
    total_questions = sum(int(item.get("question_count", 0)) for item in scoped)
    consistency_penalty = pstdev([item["score_pct"] for item in recent]) if len(recent) > 1 else 8.0
    domain_average = (
        float(domain_conf["confidence_pct"].mean())
        if not domain_conf.empty and domain_conf["attempts"].sum() > 0
        else recent_average
    )

    center = (
        recent_average * 0.34
        + overall_average * 0.18
        + domain_average * 0.24
        + readiness * 0.24
    )
    center += (self_rating_avg - 60) * 0.03
    center += min(total_questions / 140, 4.5)
    center = round(min(96.0, max(40.0, center)), 1)

    certainty_gain = min(total_questions / 35, 6.0) + min(len(scoped), 5)
    range_half = max(4.5, 15 - certainty_gain + min(consistency_penalty / 6, 4))
    range_low = round(max(30.0, center - range_half), 1)
    range_high = round(min(99.0, center + range_half), 1)

    if total_questions >= 180 and len(scoped) >= 6:
        note = "Higher confidence. The range is backed by enough question volume and recent history."
    elif total_questions >= 75:
        note = "Moderate confidence. The estimate is useful, but a few more timed attempts would tighten the range."
    else:
        note = "Low-to-moderate confidence. Treat this as directional until more quiz history is saved."

    return {
        "predicted_score": center,
        "range_low": range_low,
        "range_high": range_high,
        "confidence_note": note,
        "question_volume": total_questions,
        "history_count": len(scoped),
    }


def fatigue_breakdown(result: dict) -> dict:
    if int(result.get("question_count", 0)) < 100:
        return {}

    review = result.get("questions", [])
    if not review:
        return {}

    chunk_size = max(1, len(review) // 4)
    blocks = []
    for block_index in range(4):
        start = block_index * chunk_size
        end = len(review) if block_index == 3 else min(len(review), start + chunk_size)
        segment = review[start:end]
        if not segment:
            continue
        correct = sum(1 for item in segment if item["is_correct"])
        accuracy = round(correct / len(segment) * 100, 1)
        label = f"Q{start + 1}-{end}"
        blocks.append({"segment": label, "accuracy_pct": accuracy, "questions": len(segment)})

    topic_counter: defaultdict[tuple[str, str], int] = defaultdict(int)
    for item in review:
        if not item["is_correct"]:
            topic_counter[(item["domain"], item["topic"])] += 1

    top_missed_topics = [
        {"domain": domain, "topic": topic, "misses": misses}
        for (domain, topic), misses in sorted(topic_counter.items(), key=lambda entry: entry[1], reverse=True)[:5]
    ]

    weakest_block = min(blocks, key=lambda item: item["accuracy_pct"]) if blocks else None
    recovery_plan = [
        "Take a short break before reviewing the last 25 questions. Late-exam misses usually compound when you review immediately while mentally drained.",
        "Re-drill the top missed topics with a 10-question focused quiz within 24 hours.",
        "Run one timed 25-question recovery block to rebuild pace without repeating the full 100-question load.",
    ]
    if weakest_block and weakest_block["segment"].startswith("Q76"):
        recovery_plan.insert(0, "Your final exam block dropped hardest, so add one more late-session drill after 60-75 minutes of study.")

    return {
        "blocks": blocks,
        "top_missed_topics": top_missed_topics,
        "recovery_plan": recovery_plan,
    }


def readiness_history(exam: str, results: list[dict]) -> pd.DataFrame:
    columns = ["submitted_at", "exam", "score_pct", "readiness_score", "question_count", "mode"]
    scoped = _filter_exam(exam, results)
    if not scoped:
        return pd.DataFrame(columns=columns)

    rows = []
    cumulative: list[dict] = []
    for item in scoped:
        cumulative.append(item)
        rows.append(
            {
                "submitted_at": datetime.fromisoformat(item["submitted_at"]),
                "exam": exam,
                "score_pct": item["score_pct"],
                "readiness_score": calculate_readiness(exam, cumulative),
                "question_count": item.get("question_count", 0),
                "mode": item.get("mode", "practice"),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def readiness_trend_label(exam: str, results: list[dict], profile: dict | None = None) -> str:
    history = readiness_history(exam, results)
    if history.empty or len(history) < 2:
        return "Baseline only"
    delta = round(history.iloc[-1]["readiness_score"] - history.iloc[0]["readiness_score"], 1)
    if delta >= 8:
        return f"Up strongly (+{delta})"
    if delta >= 2:
        return f"Trending up (+{delta})"
    if delta <= -5:
        return f"Needs recovery ({delta})"
    return f"Mostly stable ({delta:+.1f})"


def build_markdown_study_summary(results: list[dict], profile: dict) -> str:
    lines = [
        "# NetSecure Study Summary",
        "",
        f"- Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}",
        f"- Target exam: {profile.get('target_exam') or 'Not set'}",
        f"- Target date: {profile.get('target_date') or 'Not set'}",
        f"- Weekly study hours: {profile.get('weekly_study_hours', 0)}",
        "",
        "## Exams Studied",
    ]

    studied_exams = [exam for exam in EXAM_DOMAINS if _filter_exam(exam, results)]
    if not studied_exams:
        lines.append("- No scored attempts saved yet.")
    for exam in studied_exams:
        scoped = _filter_exam(exam, results)
        latest_score = scoped[-1]["score_pct"] if scoped else 0.0
        readiness = calculate_readiness(exam, scoped, profile)
        lines.extend(
            [
                f"### {exam}",
                f"- Quiz count: {len(scoped)}",
                f"- Latest score: {latest_score:.1f}%",
                f"- Current readiness: {readiness:.1f}/100",
                f"- Readiness trend: {readiness_trend_label(exam, scoped, profile)}",
            ]
        )

        improved = improved_topics(exam, scoped, limit=3)
        lines.append("- Weak topics improved:")
        if improved:
            for item in improved:
                lines.append(
                    f"  - {item['topic']} ({item['domain']}): {item['start_accuracy']:.0f}% -> {item['current_accuracy']:.0f}%"
                )
        else:
            lines.append("  - No measurable topic improvement yet.")
        lines.append("")

    lines.extend(
        [
            "## LinkedIn / GitHub Blurb",
            "",
            "```md",
            f"Studying for {profile.get('target_exam') or 'multiple certifications'} with NetSecure StudyOS using local readiness tracking, quiz analytics, weak-topic recovery, and hands-on lab planning.",
            "```",
        ]
    )
    return "\n".join(lines)


def detect_misconceptions(exam: str, results: list[dict]) -> list[dict]:
    """Scan quiz history and return newly-detected misconceptions.

    A misconception is flagged when the user selects the *same* wrong answer
    option 3+ times across questions in the same domain.  Each detected
    pattern is passed to Claude to produce a targeted 3-sentence correction.
    Already-stored (unresolved) patterns are skipped to avoid duplicates.

    Returns a list of dicts ready to pass straight to save_misconception().
    """
    from collections import Counter
    from storage import misconception_already_exists, save_misconception

    scoped = _filter_exam(exam, results)
    # {(domain, topic, wrong_answer): count}
    pattern_counts: Counter = Counter()
    for result in scoped:
        for q in result.get("questions", []):
            if q.get("is_correct"):
                continue
            sel = q.get("selected_answer")
            if sel:
                pattern_counts[(q.get("domain", ""), q.get("topic", ""), sel)] += 1

    detected: list[dict] = []
    for (domain, topic, wrong_answer), count in pattern_counts.items():
        if count < 3:
            continue
        if not domain or not topic or not wrong_answer:
            continue
        if misconception_already_exists(exam, domain, topic, wrong_answer):
            continue

        correction = _get_misconception_correction(exam, domain, topic, wrong_answer)
        record = {
            "exam": exam,
            "domain": domain,
            "topic": topic,
            "wrong_pattern": wrong_answer,
            "correction": correction,
        }
        save_misconception(exam, domain, topic, wrong_answer, correction)
        detected.append(record)

    return detected


def _get_misconception_correction(exam: str, domain: str, topic: str, wrong_answer: str) -> str:
    """Call Claude to generate a targeted correction for a repeated wrong-answer pattern."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    f"This student has selected '{wrong_answer}' multiple times for questions "
                    f"about the topic '{topic}' in the '{domain}' domain of the {exam} exam. "
                    "Identify the core misconception they likely hold and generate a targeted "
                    "3-sentence correction that addresses the root cause. "
                    "Be direct, specific, and technical. Return only the 3 sentences, no headings."
                ),
            }],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        return text.strip() or _fallback_correction(topic, wrong_answer)
    except Exception:
        return _fallback_correction(topic, wrong_answer)


def _fallback_correction(topic: str, wrong_answer: str) -> str:
    return (
        f"You have repeatedly selected '{wrong_answer}' for questions about {topic}. "
        "This suggests a systematic misunderstanding of the concept. "
        "Review the official documentation and focus on distinguishing this answer from the correct one."
    )


def build_mobile_sync_payload(profile: dict, all_results: list[dict]) -> dict:
    exams_payload = {}
    for exam in EXAM_DOMAINS:
        scoped = _filter_exam(exam, all_results)
        prediction = predict_exam_score(exam, scoped, profile)
        exams_payload[exam] = {
            "readiness": calculate_readiness(exam, scoped, profile),
            "latest_score": scoped[-1]["score_pct"] if scoped else 0.0,
            "attempt_count": len(scoped),
            "prediction": prediction,
            "recommended_next_topic": recommended_next_topic(exam, scoped, profile),
            "confidence_by_domain": confidence_by_domain(exam, scoped).to_dict(orient="records"),
            "weak_topics": weakest_topics(exam, scoped, limit=6),
            "strong_topics": strongest_topics(exam, scoped, limit=6),
            "review_queue": review_queue(exam, scoped).head(8).to_dict(orient="records"),
            "study_plan": build_study_plan(exam, int(profile.get("weekly_study_hours", 8) or 8), scoped, profile),
        }
    return {
        "generated_at": datetime.now().isoformat(),
        "profile": {
            "name": profile.get("name", "Student"),
            "updated_at": profile.get("updated_at"),
            "exam_readiness": profile.get("exam_readiness", {}),
        },
        "exams": exams_payload,
    }
