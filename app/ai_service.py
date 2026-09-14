from __future__ import annotations

import os

import httpx


class OpenRouterError(RuntimeError):
    pass


def configured_models() -> list[str]:
    models = [
        os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
        os.getenv("OPENROUTER_MODEL_FALLBACK_1", "poolside/laguna-s-2.1"),
        os.getenv("OPENROUTER_MODEL_FALLBACK_2", "inclusionai/ling-3.0-flash-fin"),
    ]
    return list(dict.fromkeys(model.strip() for model in models if model.strip()))


async def chat_completion(messages: list[dict[str, str]], model: str | None = None) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise OpenRouterError("Chưa cấu hình OPENROUTER_API_KEY.")

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
        for selected_model in models:
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
                errors.append(f"{selected_model}: nội dung rỗng")
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                errors.append(f"{selected_model}: {exc}")

    raise OpenRouterError("Tất cả model OpenRouter đều thất bại: " + " | ".join(errors))