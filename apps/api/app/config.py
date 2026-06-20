from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.getenv("DATA_ROOT", REPO_ROOT / "data"))
RUNTIME_ROOT = Path(os.getenv("RUNTIME_ROOT", REPO_ROOT / "runtime"))
ARTIFACT_ROOT = RUNTIME_ROOT / "artifacts"
DB_PATH = RUNTIME_ROOT / "mona_ops.db"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-3.5-flash")
GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "models/gemini-3.1-flash-lite")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "models/gemini-3.1-flash-image")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-2")
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".png", ".jpg", ".jpeg"}

RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
