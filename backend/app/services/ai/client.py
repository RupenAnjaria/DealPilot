import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app import config

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Interface every AI-backed capability depends on.

    This is the single swap point for AI providers: add a new concrete implementation
    and wire it up in get_ai_client() below, and nothing else in the app needs to change.
    """

    @abstractmethod
    def complete_json(self, system_prompt: str, user_prompt: str) -> Optional[dict]:
        """Ask for a JSON object response. Returns None on any failure — never raises."""
        raise NotImplementedError

    @abstractmethod
    def complete_text(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Ask for a free-text response. Returns None on any failure — never raises."""
        raise NotImplementedError


class _OpenAISDKClient(AIClient):
    """Shared implementation for anything reachable through the `openai` SDK.

    Azure OpenAI and any other OpenAI-compatible endpoint only differ in how the
    underlying SDK client is constructed (see _build_azure_client / _build_openai_compatible_client
    below) — the request/response handling here is identical for both.
    """

    def __init__(self, sdk_client, model: str):
        self._sdk_client = sdk_client
        self._model = model

    def complete_json(self, system_prompt: str, user_prompt: str) -> Optional[dict]:
        content = self._complete(system_prompt, user_prompt, temperature=0, json_mode=True)
        if content is None:
            return None
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("AI returned non-JSON content; ignoring. content=%r", content[:200])
            return None
        if not isinstance(data, dict):
            logger.warning("AI JSON response was not an object; ignoring. data=%r", data)
            return None
        return data

    def complete_text(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        return self._complete(system_prompt, user_prompt, temperature=0.3, json_mode=False)

    def _complete(self, system_prompt: str, user_prompt: str, *, temperature: float, json_mode: bool) -> Optional[str]:
        try:
            extra = {"response_format": {"type": "json_object"}} if json_mode else {}
            response = self._sdk_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                timeout=config.AI_TIMEOUT_SECONDS,
                **extra,
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception:
            # Network errors, auth failures, timeouts, malformed SDK responses — all of it
            # must fall back to deterministic behavior rather than break the request.
            logger.warning("AI request failed; falling back to deterministic behavior.", exc_info=True)
            return None


def _build_azure_client() -> Optional[AIClient]:
    if not config.azure_openai_configured():
        return None
    try:
        from openai import AzureOpenAI

        sdk_client = AzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
        )
        return _OpenAISDKClient(sdk_client, model=config.AZURE_OPENAI_DEPLOYMENT)
    except Exception:
        logger.warning("Failed to construct Azure OpenAI client; running in demo mode.", exc_info=True)
        return None


def _build_openai_compatible_client() -> Optional[AIClient]:
    if not config.openai_compatible_configured():
        return None
    try:
        from openai import OpenAI

        sdk_client = OpenAI(base_url=config.OPENAI_BASE_URL, api_key=config.OPENAI_API_KEY)
        return _OpenAISDKClient(sdk_client, model=config.OPENAI_MODEL)
    except Exception:
        logger.warning("Failed to construct OpenAI-compatible client; running in demo mode.", exc_info=True)
        return None


def get_ai_client() -> Optional[AIClient]:
    """DEMO MODE vs AI MODE switch: returns None when nothing is configured, in which case
    every caller falls back to its deterministic behavior. Azure OpenAI takes priority when
    both are configured; otherwise a generic OpenAI-compatible endpoint is used.
    """
    return _build_azure_client() or _build_openai_compatible_client()
