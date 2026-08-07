from app.config import settings
from app.services import generation
from app.services.retrieval import RetrievedChunk


def test_answer_question_stream_yields_deltas_then_sources(monkeypatch):
    chunk = RetrievedChunk(
        point_id="11111111-1111-1111-1111-111111111111",
        payload={
            "element_type": "text",
            "document_name": "doc.pdf",
            "page_number": 3,
            "section_heading": "Item 1. Business",
            "text": "The company sells widgets.",
            "embedding_text": "The company sells widgets.",
        },
        score=0.05,
    )
    monkeypatch.setattr(generation, "hybrid_search", lambda question: [chunk])
    monkeypatch.setattr(
        generation.cohere_client, "rerank", lambda question, documents: [(0, 0.98)]
    )

    captured_prompt: dict[str, str] = {}

    def fake_stream_answer(system_prompt: str, user_prompt: str):
        captured_prompt["system"] = system_prompt
        captured_prompt["user"] = user_prompt
        yield "The company "
        yield "sells widgets [1]."

    monkeypatch.setattr(generation.anthropic_client, "stream_answer", fake_stream_answer)

    events = list(generation.answer_question_stream("What does the company sell?"))

    deltas = [e for e in events if e["type"] == "delta"]
    sources_events = [e for e in events if e["type"] == "sources"]

    assert [d["text"] for d in deltas] == ["The company ", "sells widgets [1]."]
    assert len(sources_events) == 1
    assert sources_events[0]["sources"] == [
        {
            "id": 1,
            "element_type": "text",
            "document_name": "doc.pdf",
            "page_number": 3,
            "section_heading": "Item 1. Business",
            "content": "The company sells widgets.",
            "image_url": None,
            "relevance_score": 0.98,
        }
    ]
    assert "[1]" in captured_prompt["user"]
    assert "The company sells widgets." in captured_prompt["user"]


def test_build_source_converts_a_chart_image_path_to_a_relative_url():
    image_path = str(settings.extracted_image_dir / "doc.pdf" / "chart-1.png")
    chunk = RetrievedChunk(
        point_id="22222222-2222-2222-2222-222222222222",
        payload={
            "element_type": "chart",
            "document_name": "doc.pdf",
            "page_number": 8,
            "section_heading": "Item 5. Market for Common Equity",
            "embedding_text": "A bar chart of quarterly revenue.",
            "image_path": image_path,
        },
        score=0.5,
    )

    source = generation._build_source(1, chunk, 0.5)

    assert source["image_url"] == "/images/doc.pdf/chart-1.png"


def test_answer_question_stream_handles_no_sources(monkeypatch):
    monkeypatch.setattr(generation, "hybrid_search", lambda question: [])
    monkeypatch.setattr(generation.cohere_client, "rerank", lambda question, documents: [])

    events = list(generation.answer_question_stream("anything"))

    assert events[0]["type"] == "delta"
    assert events[1] == {"type": "sources", "sources": []}
