from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

    def generate_json(self, prompt: str) -> str:
        # Default for providers without a strict JSON mode: plain generation.
        # The runner validates and rescues the output either way, so every
        # provider gets JSON handling instead of only the ones that override this.
        return self.generate(prompt)
