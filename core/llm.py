import uuid

import httpx

from core.config import settings


def invoke(text: str, system_prompt: str = "You are a helpful ITSM assistant.") -> str:
    headers = {"Content-Type": "application/json"}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"
        headers["x-api-key"] = settings.LLM_API_KEY

    body = {
        "action": "run",
        "modelInterface": "langchain",
        "data": {
            "mode": "chain",
            "text": text,
            "files": [],
            "modelName": settings.LLM_MODEL_NAME,
            "provider": settings.LLM_PROVIDER,
            "systemPrompt": system_prompt,
            "sessionId": str(uuid.uuid4()),
            "workspaceId": (settings.LLM_WORKSPACE_ID if settings.LLM_WORKSPACE_ID else None),
            "modelKwargs": {
                "maxTokens": 512,
                "temperature": 0.3,  # Good tradeoff between creativity and relevance
                "streaming": False,
                "topP": 0.9,
            },
        },
    }

    try:
        response = httpx.post(settings.LLM_API_URL, json=body, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()["content"]
    except httpx.HTTPError as e:
        raise RuntimeError(f"LLM unavailable: {e}") from e
