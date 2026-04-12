"""Anthropic Claude API wrapper for legal RAG generation."""
from __future__ import annotations

import logging
from typing import Iterator, Optional

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MODEL_FAST, CLAUDE_TEMPERATURE, CLAUDE_MAX_TOKENS

logger = logging.getLogger(__name__)

_client = None


def get_client() -> anthropic.Anthropic:
    """Get Anthropic client (singleton)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def generate(
    user_prompt: str,
    system_prompt: str,
    model: str = CLAUDE_MODEL,
    temperature: float = CLAUDE_TEMPERATURE,
    max_tokens: int = CLAUDE_MAX_TOKENS,
) -> str:
    """Generate a response using Claude."""
    client = get_client()
    logger.info(f"Generating response with {model} (temp={temperature})")

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text
    logger.info(f"Response generated: {len(response_text)} chars, {message.usage.output_tokens} tokens")
    return response_text


def generate_fast(
    user_prompt: str,
    system_prompt: str,
    max_tokens: int = 300,
) -> str:
    """Generate a quick response using the fast model (Sonnet). For query rewriting, follow-ups, etc."""
    return generate(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model=CLAUDE_MODEL_FAST,
        max_tokens=max_tokens,
    )


def stream_response(
    user_prompt: str,
    system_prompt: str,
    model: str = CLAUDE_MODEL,
    temperature: float = CLAUDE_TEMPERATURE,
    max_tokens: int = CLAUDE_MAX_TOKENS,
) -> Iterator[str]:
    """Stream a response from Claude, yielding text chunks."""
    client = get_client()
    logger.info(f"Streaming response with {model}")

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def stream_with_history(
    messages: list[dict],
    system_prompt: str,
    model: str = CLAUDE_MODEL,
    temperature: float = CLAUDE_TEMPERATURE,
    max_tokens: int = CLAUDE_MAX_TOKENS,
) -> Iterator[str]:
    """Stream a response with conversation history, yielding text chunks."""
    client = get_client()
    logger.info(f"Streaming response with history ({len(messages)} messages)")

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text


def generate_with_history(
    messages: list[dict],
    system_prompt: str,
    model: str = CLAUDE_MODEL,
    temperature: float = CLAUDE_TEMPERATURE,
    max_tokens: int = CLAUDE_MAX_TOKENS,
) -> str:
    """Generate with full conversation history."""
    client = get_client()

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=messages,
    )

    return message.content[0].text
