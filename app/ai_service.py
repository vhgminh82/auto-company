from __future__ import annotations

import asyncio
import os
import time

import httpx


class OpenRouterError(RuntimeError):
    pass


_FREE_MODELS_CACHE: tuple[float, list[str]] = (0.0, [])
_FREE_MODELS_LOCK = asyncio.Lock()
_FREE_MODELS_TTL_SECONDS = 600
_FREE_MODELS_LIMIT = 5


def configured_models() -> list[str]:
    models = [
        os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
        os.getenv("OPENROUTER_MODEL_FALLBACK_1", "poolside/laguna-s-2.1"),
        os.getenv("OPENROUTER_MODEL_FALLBACK_2", "inclusionai/ling-3.0-flash-fin"),
    ]
    return list(dict.fromkeys(model.strip() for model in models if model.strip()))


async def _free_models(client: httpx.AsyncClient, headers: dict[str, str]) -> list[str]:
    global _FREE_MODELS_CACHE
    cached_at, cached_models = _FREE_MODELS_CACHE
    if cached_models and time.monotonic() - cached_at < _FREE_MODELS_TTL_SECONDS:
        return cached_models

    async with _FREE_MODELS_LOCK:
        cached_at, cached_models = _FREE_MODELS_CACHE
        if cached_models and time.monotonic() - cached_at < _FREE_MODELS_TTL_SECONDS:
            return cached_models
        try:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                params={"output_modalities": "text", "sort": "most-popular"},
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            candidates: list[str] = []
            for item in data:
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                pricing = item.get("pricing") or {}
                try:
                    is_free = float(pricing.get("prompt", 1)) == 0 and float(pricing.get("completion", 1)) == 0
                except (TypeError, ValueError):
                    is_free = False
                modalities = (item.get("architecture") or {}).get("output_modalities") or []
                context_length = int(item.get("context_length") or 0)
                if (is_free or str(item["id"]).endswith(":free")) and (not modalities or "text" in modalities) and context_length >= 8192:
                    candidates.append(str(item["id"]))
            _FREE_MODELS_CACHE = (time.monotonic(), candidates[:_FREE_MODELS_LIMIT])
            return _FREE_MODELS_CACHE[1]
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return []


async def chat_completion(messages: list[dict[str, str]], model: str | None = None) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://127.0.0.1:8000"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "Company Crawl Platform"),
    }

    models = [model.strip()] if model else configured_models()
    max_tokens = max(256, min(int(os.getenv("OPENROUTER_MAX_TOKENS", "2048")), 8192))
    errors: list[str] = []
    async with httpx.AsyncClient(timeout=60) as client:
        attempted: set[str] = set()

        async def try_models(candidates: list[str]) -> str | None:
            for selected_model in candidates:
                if selected_model in attempted:
                    continue
                attempted.add(selected_model)
                payload = {"model": selected_model, "messages": messages, "temperature": 0.2, "max_tokens": max_tokens}
                try:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if response.is_error:
                        errors.append(f"{selected_model}: HTTP {response.status_code} {response.text[:300]}")
                        continue
                    content = response.json()["choices"][0]["message"]["content"]
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                    errors.append(f"{selected_model}: empty content")
                except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                    errors.append(f"{selected_model}: {exc}")
            return None

        content = await try_models(models)
        if content is not None:
            return content

        content = await try_models(await _free_models(client, headers))
        if content is not None:
            return content

    raise OpenRouterError("All OpenRouter models failed: " + " | ".join(errors))
