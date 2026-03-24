"""
Client helpers for the local AI explanation workflows.

This module talks to a local Ollama server and requests structured output
for grounded explanation tasks. The first implementations are intentionally
simple and focused on one-shot summary and comparison calls.
"""

from __future__ import annotations

import httpx

from app.schemas.ai_summary import AIComparisonSummaryOutput, AISummaryOutput


def _generate_structured_response(
    prompt: str,
    schema: dict,
    model: str,
    base_url: str,
    timeout_seconds: int,
) -> str:
    """
    Request a structured response from Ollama using a JSON schema.

    Args:
        prompt: Prompt text for the model.
        schema: JSON schema used to constrain the response.
        model: Ollama model name.
        base_url: Ollama server base URL.
        timeout_seconds: HTTP timeout.

    Returns:
        The raw JSON string returned in Ollama's `response` field.

    Raises:
        ValueError: If Ollama does not return the expected response payload.
    """
    request_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": schema,
        "options": {
            "temperature": 0,
        },
    }

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(f"{base_url}/api/generate", json=request_payload)
        response.raise_for_status()
        payload = response.json()

    raw_response_text = payload.get("response")
    if not raw_response_text:
        raise ValueError("Ollama response did not contain a structured 'response' field.")

    return raw_response_text


def generate_structured_ai_summary(
    prompt: str,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    timeout_seconds: int = 60,
) -> AISummaryOutput:
    """
    Request a structured single-result AI explanation from Ollama.

    Args:
        prompt: Grounded prompt text built from deterministic findings.
        model: Local Ollama model name to use.
        base_url: Ollama server base URL.
        timeout_seconds: Request timeout.

    Returns:
        A validated AISummaryOutput object.
    """
    raw_response_text = _generate_structured_response(
        prompt=prompt,
        schema=AISummaryOutput.model_json_schema(),
        model=model,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
    )
    return AISummaryOutput.model_validate_json(raw_response_text)


def generate_structured_ai_comparison_summary(
    prompt: str,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    timeout_seconds: int = 60,
) -> AIComparisonSummaryOutput:
    """
    Request a structured before/after AI comparison explanation from Ollama.

    Args:
        prompt: Grounded prompt text built from deterministic before/after findings.
        model: Local Ollama model name to use.
        base_url: Ollama server base URL.
        timeout_seconds: Request timeout.

    Returns:
        A validated AIComparisonSummaryOutput object.
    """
    raw_response_text = _generate_structured_response(
        prompt=prompt,
        schema=AIComparisonSummaryOutput.model_json_schema(),
        model=model,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
    )
    return AIComparisonSummaryOutput.model_validate_json(raw_response_text)