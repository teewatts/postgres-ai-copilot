"""
Client helpers for the local AI explanation workflow.

This module talks to a local Ollama server and requests structured output
for grounded explanation tasks. The first implementation is intentionally
simple and focused on a single one-shot explanation call.
"""

from __future__ import annotations

import httpx

from app.schemas.ai_summary import AISummaryOutput


def generate_structured_ai_summary(
    prompt: str,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    timeout_seconds: int = 60,
) -> AISummaryOutput:
    """
    Request a structured AI explanation from Ollama.

    Args:
        prompt: Grounded prompt text built from deterministic findings.
        model: Local Ollama model name to use.
        base_url: Ollama server base URL.
        timeout_seconds: Request timeout.

    Returns:
        A validated AISummaryOutput object.

    Raises:
        ValueError: If the Ollama response is missing the expected fields.
    """
    request_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": AISummaryOutput.model_json_schema(),
    }

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(f"{base_url}/api/generate", json=request_payload)
        response.raise_for_status()
        payload = response.json()

    raw_response_text = payload.get("response")
    if not raw_response_text:
        raise ValueError("Ollama response did not contain a structured 'response' field.")

    return AISummaryOutput.model_validate_json(raw_response_text)