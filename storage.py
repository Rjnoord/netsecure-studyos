from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import re
from uuid import uuid4

import pandas as pd

from exams import EXAM_DOMAINS


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = DATA_DIR / "results"
EXPORTS_DIR = DATA_DIR / "exports"
SESSIONS_DIR = DATA_DIR / "sessions"
PROFILE_PATH = DATA_DIR / "user_profile.json"
MOBILE_SYNC_PATH = DATA_DIR / "mobile_sync.json"
MOBILE_APP_SYNC_PATH = BASE_DIR / "mobile_app" / "data" / "mobile_sync.json"


def _safe_filename(filename: str, suffix: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", filename).strip("._")
    if not cleaned:
        cleaned = f"export{suffix}"
    if not cleaned.endswith(suffix):
        cleaned = f"{cleaned}{suffix}"
    return cleaned


def _atomic_write_json(destination: Path, payload: dict) -> None:
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    temp_path.replace(destination)


def _atomic_write_text(destination: Path, content: str) -> None:
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(content)
    temp_path.replace(destination)


def default_profile() -> dict:
    return {
        "name": "Student",
        "exam_readiness": {},
        "updated_at": None,
        "onboarding_complete": False,
        "target_exam": None,
        "target_date": None,
        "weekly_study_hours": 6,
        "domain_self_ratings": {exam: {domain: 3 for domain in domains} for exam, domains in EXAM_DOMAINS.items()},
        "lab_progress": {},
        "auth": {
            "passcode_hash": None,
            "passcode_salt": None,
            "failed_attempts": 0,
            "lockout_until": None,
            "updated_at": None,
        },
        "links": {
            "public_app_url": None,
            "mobile_app_url": None,
        },
    }


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def ensure_storage() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    MOBILE_APP_SYNC_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PROFILE_PATH.exists():
        save_user_profile(default_profile())


def load_user_profile() -> dict:
    ensure_storage()
    with PROFILE_PATH.open("r", encoding="utf-8") as handle:
        profile = json.load(handle)
    normalized = _deep_merge(default_profile(), profile)
    if normalized != profile:
        save_user_profile(normalized)
    return normalized


def save_user_profile(profile: dict) -> None:
    ensure_storage()
    normalized = _deep_merge(default_profile(), profile)
    _atomic_write_json(PROFILE_PATH, normalized)


def load_results(exam: str | None = None) -> list[dict]:
    ensure_storage()
    results = []
    for file_path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if exam and payload.get("exam") != exam:
                continue
            results.append(payload)
        except (json.JSONDecodeError, OSError):
            continue
    results.sort(key=lambda item: item.get("submitted_at", ""))
    return results


def save_quiz_result(result: dict) -> Path:
    ensure_storage()
    stamp = result.get("submitted_at", "").replace(":", "-")
    filename = f"{stamp}_{uuid4().hex[:8]}.json"
    destination = RESULTS_DIR / filename
    _atomic_write_json(destination, result)
    return destination


def export_dataframe(frame: pd.DataFrame, filename: str) -> Path:
    ensure_storage()
    destination = EXPORTS_DIR / _safe_filename(filename, ".csv")
    frame.to_csv(destination, index=False)
    return destination


def export_markdown(content: str, filename: str) -> Path:
    ensure_storage()
    destination = EXPORTS_DIR / _safe_filename(filename, ".md")
    _atomic_write_text(destination, content)
    return destination


def save_active_session(session: dict) -> Path:
    ensure_storage()
    destination = SESSIONS_DIR / f"{session['session_id']}.json"
    _atomic_write_json(destination, session)
    return destination


def load_active_sessions() -> list[dict]:
    ensure_storage()
    sessions = []
    for file_path in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                sessions.append(json.load(handle))
        except (json.JSONDecodeError, OSError):
            continue
    sessions.sort(key=lambda item: item.get("started_at", ""))
    return sessions


def delete_active_session(session_id: str) -> None:
    destination = SESSIONS_DIR / f"{session_id}.json"
    if destination.exists():
        destination.unlink()


def save_mobile_sync(payload: dict) -> None:
    ensure_storage()
    for destination in [MOBILE_SYNC_PATH, MOBILE_APP_SYNC_PATH]:
        _atomic_write_json(destination, payload)


def build_quiz_history_frame(results: list[dict]) -> pd.DataFrame:
    columns = [
        "submitted_at",
        "exam",
        "mode",
        "question_count",
        "correct_count",
        "score_pct",
        "timed_mode",
        "minutes_allocated",
        "elapsed_seconds",
    ]
    rows = []
    for result in results:
        rows.append(
            {
                "submitted_at": result.get("submitted_at"),
                "exam": result.get("exam"),
                "mode": result.get("mode"),
                "question_count": result.get("question_count"),
                "correct_count": result.get("correct_count"),
                "score_pct": result.get("score_pct"),
                "timed_mode": result.get("timed_mode"),
                "minutes_allocated": result.get("minutes_allocated"),
                "elapsed_seconds": result.get("elapsed_seconds"),
            }
        )
    return pd.DataFrame(rows, columns=columns)
