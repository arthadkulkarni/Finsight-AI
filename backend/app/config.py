from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # OpenAI's text-embedding-3-small — fixed here because the Qdrant
    # collection's vector size is created to match it.
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    claude_model: str = "claude-sonnet-5"

    upload_dir: Path = BACKEND_DIR / "data" / "uploads"
    extracted_image_dir: Path = BACKEND_DIR / "data" / "images"
    qdrant_path: Path = BACKEND_DIR / "data" / "qdrant"
    qdrant_collection: str = "filings"


settings = Settings()
