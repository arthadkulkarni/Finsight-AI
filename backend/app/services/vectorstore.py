from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, ScoredPoint, VectorParams

from app.config import settings
from app.models.elements import ParsedElement

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    """Connect to a real Qdrant server when QDRANT_URL is set (Docker
    Compose); otherwise fall back to local embedded mode, which writes to a
    folder on disk instead of talking to a server. Same client API either
    way. Local mode only allows one process to hold its storage directory
    open at a time — fine for a single bare-metal process, but breaks the
    moment a separate API process and worker process both need it, which is
    exactly why Compose runs a real server instead.
    """
    global _client
    if _client is None:
        if settings.qdrant_url:
            _client = QdrantClient(url=settings.qdrant_url)
        else:
            settings.qdrant_path.mkdir(parents=True, exist_ok=True)
            _client = QdrantClient(path=str(settings.qdrant_path))
    return _client


def ensure_collection() -> None:
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )


def upsert_elements(elements: list[ParsedElement]) -> int:
    """Store each element's embedding as a vector, with everything else
    (document name, page number, element type, section heading, original
    content) as payload — retrieval needs the original content to cite it,
    not just the embedding.
    """
    ensure_collection()
    points = [
        PointStruct(
            id=element.element_id,
            vector=element.embedding,
            payload=element.model_dump(mode="json", exclude={"embedding"}),
        )
        for element in elements
        if element.embedding is not None
    ]
    if points:
        get_client().upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def search(query_vector: list[float], limit: int = 10) -> list[ScoredPoint]:
    ensure_collection()
    response = get_client().query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        limit=limit,
    )
    return response.points
