from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.getenv("DATA_ROOT", REPO_ROOT / "data"))
RUNTIME_ROOT = Path(os.getenv("RUNTIME_ROOT", REPO_ROOT / "runtime"))
ARTIFACT_ROOT = RUNTIME_ROOT / "artifacts"
DB_PATH = RUNTIME_ROOT / "mona_ops.db"
# GEMINI_MODEL is the generic override; GEMINI_FAST_MODEL stays as the workflow default.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip()
GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "").strip() or GEMINI_MODEL or "models/gemini-3.1-flash-lite"
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "models/gemini-3.1-flash-image")
# Rate-limit resilience: bounded exponential backoff + concurrency cap for batch fan-out.
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "4"))
GEMINI_MAX_CONCURRENCY = int(os.getenv("GEMINI_MAX_CONCURRENCY", "5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".png", ".jpg", ".jpeg"}
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
