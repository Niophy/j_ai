# import os
# from src.core.base_provider import BaseProvider
# from src.providers.ollama_provider import OllamaProvider

# def get_provider() -> BaseProvider:
#    provider_name = os.getenv("JAI_PROVIDER", "ollama").lower()

#    if provider_name == "ollama":
#        return OllamaProvider()

#    raise ValueError(f"Unknown provider: {provider_name}")

import os
from src.core.base_provider import BaseProvider
from src.providers.ollama_provider import OllamaProvider
from src.providers.gpt_provider import GPTProvider

def get_provider() -> BaseProvider:
    provider_name = os.getenv("JAI_PROVIDER", "ollama").lower()

    if provider_name == "ollama":
        return OllamaProvider()

    if provider_name == "gpt":
        return GPTProvider()

    raise ValueError(f"Unknown provider: {provider_name}")
