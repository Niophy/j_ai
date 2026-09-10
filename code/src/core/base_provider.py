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

    def chat(self, messages: list, tools: list | None = None, options: dict | None = None) -> dict:
        # Multi-turn chat with optional tool calling. Returns the assistant message
        # dict ({"role", "content", and "tool_calls" when the model wants a tool}).
        # Only providers with a chat endpoint override this; the agent loop needs it.
        raise NotImplementedError(f"{type(self).__name__} has no chat/tool-calling support")
