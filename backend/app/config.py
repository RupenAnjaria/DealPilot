import os

from dotenv import load_dotenv

load_dotenv()

# DEMO MODE (default on): forces the app to run fully deterministically — no AI client is
# ever constructed, regardless of which AI credentials happen to be set below. This is the
# reliability guarantee for a live demo recording: it can never fail, stall, or produce a
# different answer because of an AI provider, even if Azure/OpenAI vars are left configured
# in the environment from earlier testing. Set DEMO_MODE=false to actually exercise AI MODE.
DEMO_MODE = os.getenv("DEMO_MODE", "true").strip().lower() not in ("false", "0", "no")

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

