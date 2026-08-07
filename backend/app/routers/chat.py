import json
from collections.abc import Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.generation import answer_question_stream

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
async def chat(payload: ChatRequest) -> StreamingResponse:
    def event_stream() -> Generator[str, None, None]:
        try:
            for event in answer_question_stream(payload.question):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:  # reported to the client as an SSE event, not swallowed
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            return
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
