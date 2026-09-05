from app import config
from app.services.ai import client as ai_client


def test_demo_mode_defaults_to_on() -> None:
    # No DEMO_MODE=false is set in this environment/.env, so the safe default must hold.
    assert config.DEMO_MODE is True


def test_get_ai_client_returns_none_when_nothing_configured(monkeypatch) -> None:
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", None)
    monkeypatch.setattr(config, "AZURE_OPENAI_API_KEY", None)
    monkeypatch.setattr(config, "AZURE_OPENAI_DEPLOYMENT", None)
    monkeypatch.setattr(config, "OPENAI_BASE_URL", None)
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    monkeypatch.setattr(config, "OPENAI_MODEL", None)
    assert ai_client.get_ai_client() is None


def test_get_ai_client_returns_none_when_demo_mode_is_on_even_if_configured(monkeypatch) -> None:
    monkeypatch.setattr(config, "DEMO_MODE", True)
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setattr(config, "AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setattr(config, "AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    calls = []
    monkeypatch.setattr("openai.AzureOpenAI", lambda **kwargs: calls.append("azure") or object())

    assert ai_client.get_ai_client() is None
    assert calls == []


def test_get_ai_client_prefers_azure_when_both_configured(monkeypatch) -> None:
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setattr(config, "AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setattr(config, "AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setattr(config, "OPENAI_BASE_URL", "https://example.local/v1")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "generic-key")
    monkeypatch.setattr(config, "OPENAI_MODEL", "some-model")

    calls = []
    monkeypatch.setattr("openai.AzureOpenAI", lambda **kwargs: calls.append(("azure", kwargs)) or object())
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: calls.append(("openai", kwargs)) or object())

    result = ai_client.get_ai_client()
    assert result is not None
    assert calls[0][0] == "azure"


def test_get_ai_client_falls_back_to_openai_compatible(monkeypatch) -> None:
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", None)
    monkeypatch.setattr(config, "AZURE_OPENAI_API_KEY", None)
    monkeypatch.setattr(config, "AZURE_OPENAI_DEPLOYMENT", None)
    monkeypatch.setattr(config, "OPENAI_BASE_URL", "https://example.local/v1")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "generic-key")
    monkeypatch.setattr(config, "OPENAI_MODEL", "some-model")

    calls = []
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: calls.append(("openai", kwargs)) or object())

    result = ai_client.get_ai_client()
    assert result is not None
    assert calls[0][0] == "openai"


def test_azure_client_construction_failure_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setattr(config, "AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setattr(config, "AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setattr(config, "OPENAI_BASE_URL", None)
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    monkeypatch.setattr(config, "OPENAI_MODEL", None)

    def _boom(**kwargs):
        raise RuntimeError("bad credentials")

    monkeypatch.setattr("openai.AzureOpenAI", _boom)
    assert ai_client.get_ai_client() is None


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content=None, raise_error=None):
        self._content = content
        self._raise_error = raise_error

    def create(self, **kwargs):
        if self._raise_error:
            raise self._raise_error
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, **kwargs):
        self.completions = _FakeCompletions(**kwargs)


class _FakeSDKClient:
    def __init__(self, **kwargs):
        self.chat = _FakeChat(**kwargs)


def test_complete_json_parses_valid_json_object() -> None:
    sdk_client = _FakeSDKClient(content='{"brand": "Nike", "max_price": 120}')
    wrapped = ai_client._OpenAISDKClient(sdk_client, model="test-model")
    result = wrapped.complete_json("system", "user")
    assert result == {"brand": "Nike", "max_price": 120}


def test_complete_json_returns_none_for_invalid_json() -> None:
    sdk_client = _FakeSDKClient(content="not json at all")
    wrapped = ai_client._OpenAISDKClient(sdk_client, model="test-model")
    assert wrapped.complete_json("system", "user") is None


def test_complete_json_returns_none_for_non_object_json() -> None:
    sdk_client = _FakeSDKClient(content="[1, 2, 3]")
    wrapped = ai_client._OpenAISDKClient(sdk_client, model="test-model")
    assert wrapped.complete_json("system", "user") is None


def test_complete_json_returns_none_when_content_missing() -> None:
    sdk_client = _FakeSDKClient(content=None)
    wrapped = ai_client._OpenAISDKClient(sdk_client, model="test-model")
    assert wrapped.complete_json("system", "user") is None


def test_complete_text_strips_whitespace() -> None:
    sdk_client = _FakeSDKClient(content="  hello there  ")
    wrapped = ai_client._OpenAISDKClient(sdk_client, model="test-model")
    assert wrapped.complete_text("system", "user") == "hello there"


def test_complete_returns_none_when_sdk_call_raises() -> None:
    sdk_client = _FakeSDKClient(raise_error=RuntimeError("network down"))
    wrapped = ai_client._OpenAISDKClient(sdk_client, model="test-model")
    assert wrapped.complete_json("system", "user") is None
    assert wrapped.complete_text("system", "user") is None
