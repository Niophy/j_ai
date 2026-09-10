import os
from src.core.base_provider import BaseProvider
from src.providers.ollama_provider import OllamaProvider
from src.providers.gpt_provider import GPTProvider


def get_provider(role: str | None = None) -> BaseProvider:
    """Build the configured provider, optionally for a named role.

    Roles let the judge and the student run on different models and thinking
    settings (2026-09-10, model bake-off). JAI_JUDGE_MODEL / JAI_STUDENT_MODEL
    override JAI_OLLAMA_MODEL; JAI_JUDGE_THINK / JAI_STUDENT_THINK override
    JAI_THINK. With no role, or no override set, the plain defaults apply.
    """
    provider_name = os.getenv("JAI_PROVIDER", "ollama").lower()

    if provider_name == "ollama":
        model = None
        think = None
        if role:
            prefix = f"JAI_{role.upper()}_"
            model = os.getenv(prefix + "MODEL") or None
            think = os.getenv(prefix + "THINK") or None
        return OllamaProvider(model=model, think=think)

    if provider_name == "gpt":
        return GPTProvider()

    raise ValueError(f"Unknown provider: {provider_name}")
