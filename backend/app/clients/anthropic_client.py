import base64
from pathlib import Path

import anthropic

from app.config import settings

_client: anthropic.Anthropic | None = None

_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to backend/.env to enable "
                "table summarization and chart descriptions."
            )
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def summarize_table(table_html: str) -> str:
    """Turn a financial table's HTML into a natural-language summary suitable
    for embedding — dense HTML embeds poorly, a plain-English description of
    what the table shows and its key figures embeds well.
    """
    response = _get_client().messages.create(
        model=settings.claude_model,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarize the following financial table in a few sentences of "
                    "plain English. Mention what the table covers and its key "
                    "figures, so the summary alone conveys what's in the table.\n\n"
                    f"{table_html}"
                ),
            }
        ],
    )
    return _first_text(response)


def describe_chart(image_path: str) -> str:
    """Describe a chart/figure image via Claude vision, for embedding."""
    image_bytes = Path(image_path).read_bytes()
    media_type = _MEDIA_TYPES.get(Path(image_path).suffix.lower(), "image/png")

    response = _get_client().messages.create(
        model=settings.claude_model,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Describe this chart or figure from a financial filing in "
                            "a few sentences of plain English, including what it "
                            "measures and any notable values or trends."
                        ),
                    },
                ],
            }
        ],
    )
    return _first_text(response)


def _first_text(response: anthropic.types.Message) -> str:
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""
