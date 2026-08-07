from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    cohere_api_key: str | None = None

    # OpenAI's text-embedding-3-small — fixed here because the Qdrant
    # collection's vector size is created to match it.
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    claude_model: str = "claude-sonnet-5"
    cohere_rerank_model: str = "rerank-v4.0-pro"

    upload_dir: Path = BACKEND_DIR / "data" / "uploads"
    extracted_image_dir: Path = BACKEND_DIR / "data" / "images"
    qdrant_path: Path = BACKEND_DIR / "data" / "qdrant"
    qdrant_collection: str = "filings"
    # When set (e.g. by docker-compose), connect to a real Qdrant server
    # instead of local embedded mode. Local mode locks its storage directory
    # to a single process, which breaks the moment the API and Celery worker
    # need to read it at the same time — a real server is what Compose gives
    # both containers to talk to instead.
    qdrant_url: str | None = None

    redis_url: str = "redis://localhost:6379/0"

    # Retrieval tuning: candidates pulled from each retriever before fusion,
    # candidates kept after fusion, and final sources kept after rerank.
    dense_search_k: int = 20
    bm25_search_k: int = 20
    fused_k: int = 20
    rerank_top_n: int = 5


settings = Settings()
