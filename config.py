from __future__ import annotations

FREE_TIER: dict = {
    "allowed_exams": ["A+", "Network+", "Security+"],
    "daily_question_limit": 10,
    "labs_per_cert": 1,
    "ai_tutor": False,
    "ai_lab_grader": False,
    "resume_builder": False,
    "linkedin_poster": False,
    "career_dashboard": False,
    "skill_tree_full": False,
    "boss_battle": False,
    "daily_challenge_leaderboard": False,
    "debate_mode": False,
    "exports": False,
}

PRO_TIER: dict = {
    "allowed_exams": "all",
    "daily_question_limit": None,
    "labs_per_cert": None,
    "ai_tutor": True,
    "ai_lab_grader": True,
    "resume_builder": True,
    "linkedin_poster": True,
    "career_dashboard": True,
    "skill_tree_full": True,
    "boss_battle": True,
    "daily_challenge_leaderboard": True,
    "debate_mode": True,
    "exports": True,
}

TIERS: dict[str, dict] = {
    "free": FREE_TIER,
    "pro": PRO_TIER,
}

# Human-readable feature names for upgrade prompts
FEATURE_LABELS: dict[str, str] = {
    "ai_tutor": "AI Tutor",
    "ai_lab_grader": "AI Lab Grader",
    "resume_builder": "Resume Builder",
    "linkedin_poster": "LinkedIn Auto-Poster",
    "career_dashboard": "Career & Salary Dashboard",
    "skill_tree_full": "Full Skill Tree",
    "boss_battle": "Boss Battle Mode",
    "daily_challenge_leaderboard": "Daily Challenge Leaderboard",
    "debate_mode": "Debate Mode",
    "exports": "Data Exports",
}
