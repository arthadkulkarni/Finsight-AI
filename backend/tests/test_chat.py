from fastapi.testclient import TestClient

import app.routers.chat as chat_module
from app.main import app

client = TestClient(app)


def test_chat_streams_deltas_then_sources_then_done(monkeypatch):
    def fake_stream(question: str):
        yield {"type": "delta", "text": "The company "}
        yield {"type": "delta", "text": "sells widgets [1]."}
        yield {"type": "sources", "sources": [{"id": 1}]}

    monkeypatch.setattr(chat_module, "answer_question_stream", fake_stream)

    response = client.post("/chat", json={"question": "What does the company sell?"})

    assert response.status_code == 200
    lines = response.text.splitlines()
    events = [line.removeprefix("data: ") for line in lines if line.startswith("data: ")]
    assert events[0] == '{"type": "delta", "text": "The company "}'
    assert events[-2] == '{"type": "sources", "sources": [{"id": 1}]}'
    assert events[-1] == '{"type": "done"}'


def test_chat_reports_errors_as_an_sse_event_instead_of_crashing(monkeypatch):
    def fake_stream(question: str):
        yield {"type": "delta", "text": "partial answer "}
        raise RuntimeError("OPENAI_API_KEY is not set.")

    monkeypatch.setattr(chat_module, "answer_question_stream", fake_stream)

    response = client.post("/chat", json={"question": "anything"})

    assert response.status_code == 200
    assert '"type": "error"' in response.text
    assert "OPENAI_API_KEY is not set." in response.text
    assert '"type": "done"' not in response.text
