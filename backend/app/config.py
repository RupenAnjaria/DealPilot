import os

from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI (optional) — takes priority when configured alongside the generic settings below.
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

# Any other OpenAI-compatible endpoint (OpenAI itself, Azure AI Foundry Local, a local
# vLLM/Ollama server, etc.), used only when the Azure settings above aren't set.
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

# Per-request timeout (seconds) for any AI call, so a slow/unreachable endpoint can never
# stall a request — the app always falls back to deterministic behavior instead.
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "5"))


def azure_openai_configured() -> bool:
    """AI features are optional — the app must work fully without these being set."""
    return bool(AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT)


def openai_compatible_configured() -> bool:
    """Whether a generic OpenAI-compatible endpoint (non-Azure) is fully configured."""
    return bool(OPENAI_BASE_URL and OPENAI_API_KEY and OPENAI_MODEL)

