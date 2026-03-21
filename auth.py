from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta


PBKDF2_ITERATIONS = 200_000
LOCKOUT_MINUTES = 5
MAX_FAILED_ATTEMPTS = 5


def hash_passcode(passcode: str, salt: str | None = None) -> tuple[str, str]:
    chosen_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        passcode.encode("utf-8"),
        chosen_salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return digest, chosen_salt


def verify_passcode(passcode: str, passcode_hash: str, salt: str) -> bool:
    candidate_hash, _ = hash_passcode(passcode, salt)
    return secrets.compare_digest(candidate_hash, passcode_hash)


def passcode_feedback(passcode: str) -> list[str]:
    issues = []
    cleaned = passcode.strip()
    if len(cleaned) < 8:
        issues.append("Use at least 8 characters.")
    if cleaned.lower() == cleaned or cleaned.upper() == cleaned:
        issues.append("Mix upper and lower case letters.")
    if not any(char.isdigit() for char in cleaned):
        issues.append("Include at least one number.")
    return issues


def lockout_expiry_iso() -> str:
    return (datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()


def is_locked_until(lockout_until: str | None) -> bool:
    if not lockout_until:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(lockout_until)
    except ValueError:
        return False
