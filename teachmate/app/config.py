"""Settings for the TeachMate service, read from the repo-root .env (shared with the Node app)."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

# The Node app's GOOGLE_API_KEY is a YouTube key (often still a "<placeholder>");
# hide placeholders so the google-genai SDK doesn't pick them up instead of GEMINI_API_KEY.
if os.environ.get("GOOGLE_API_KEY", "").startswith("<"):
    os.environ.pop("GOOGLE_API_KEY")


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _key(name: str) -> str:
    """An API key from the environment; an unfilled "<placeholder>" copied from .env.example counts as missing."""
    value = os.getenv(name, "").strip()
    return "" if value.startswith("<") else value


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = _key("GEMINI_API_KEY")
    # Primary model first; the rest are tried in order when a model is overloaded or rate-limited.
    gemini_models: list[str] = field(
        default_factory=lambda: [os.getenv("GEMINI_MODEL", "gemini-3.8-flash")]
        + _split(os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.6-flash,gemini-3.5-flash-lite"))
    )
    tcherly_api_url: str = os.getenv("TCHERLY_API_URL", "http://localhost:3000/api").rstrip("/")
    max_tool_rounds: int = int(os.getenv("TEACHMATE_MAX_TOOL_ROUNDS", "5"))
    # Per Gemini call; a hung or very slow model is abandoned for the next fallback model.
    model_timeout_s: float = float(os.getenv("TEACHMATE_MODEL_TIMEOUT_S", "45"))
    # Same database and JWT secret as the Node app (see config/index.js for the matching defaults).
    mongo_uri: str = os.getenv("DB_URI", "mongodb://localhost:27017/test-debe")
    jwt_secret: str = os.getenv("JWT_SECRET", "setup_dotenv_file_for_security")
    cors_origins: list[str] = field(
        default_factory=lambda: _split(os.getenv("TEACHMATE_CORS_ORIGINS", "http://localhost:8080"))
    )


settings = Settings()
