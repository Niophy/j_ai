import json
import os
import requests

from src.core.base_provider import BaseProvider
from src.core.jsonx import extract_first_json_object as _extract_first_json_object


def _looks_like_json_request(prompt: str) -> bool:
    """
    Heuristic. If prompt asks for JSON, we switch to strict JSON mode.
    """
    p = (prompt or "").lower()
    if "return only valid json" in p:
        return True
    if "return only json" in p:
        return True
    if "json" in p and ("return" in p or "output" in p):
        return True
    return False


def parse_think(value):
    """Env string -> Ollama 'think' value. Unset means: do not send the field.

    Booleans switch thinking on/off for models that support it (qwen3 family);
    gpt-oss only understands effort levels (low / medium / high). Sending the
    field to a model without thinking support is an error, so None is the
    default and the field is only sent when configured.
    """
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ("", "none", "unset"):
        return None
    if v in ("1", "true", "on", "yes"):
        return True
    if v in ("0", "false", "off", "no"):
        return False
    return v  # low / medium / high / max


class OllamaProvider(BaseProvider):

    def __init__(self, base_url: str | None = None, model: str | None = None, think=None):
        self.base_url = base_url or os.getenv("JAI_OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("JAI_OLLAMA_MODEL", "llama3")
        self.think = parse_think(think if think is not None else os.getenv("JAI_THINK"))

        self.timeout_seconds = int(os.getenv("JAI_OLLAMA_TIMEOUT", "120"))
        self.temperature = float(os.getenv("JAI_TEMPERATURE", "0.2"))
        self.num_predict = int(os.getenv("JAI_MAX_TOKENS", "512"))

        self.json_retries = int(os.getenv("JAI_JSON_RETRIES", "2"))
        # Budget for schema-enforced verdicts. Thinking models spend tokens on
        # the trace before the JSON and the schema cannot constrain that part;
        # qwen3.8 at 1024 truncated 3 of 17 verdicts (2026-09-10).
        self.structured_max_tokens = int(os.getenv("JAI_STRUCTURED_MAX_TOKENS", "4096"))
        # Schema-enforced output is the default; JAI_STRUCTURED=0 returns to
        # prompt-only JSON plus retry/rescue (the pre-2026-09-10 path).
        self.structured = os.getenv("JAI_STRUCTURED", "1") != "0"

        self.system_default = os.getenv(
            "JAI_SYSTEM_DEFAULT",
            "You are J_AI. Be precise. If asked for JSON, output only JSON."
        )

    # ------------------------------------------------------------------ HTTP

    def _options(self, options):
        final_options = {
            "temperature": self.temperature,
            "num_predict": self.num_predict,
        }
        if options:
            final_options.update(options)
        return final_options

    def _post(self, path, payload):
        response = requests.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout_seconds)
        if response.status_code != 200:
            raise RuntimeError(f"Ollama error {response.status_code}: {response.text}")
        return response.json()

    def _post_generate(self, prompt: str, system: str | None, options: dict | None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": self._options(options),
        }
        if system:
            payload["system"] = system
        if self.think is not None:
            payload["think"] = self.think
        data = self._post("/api/generate", payload)
        return (data.get("response", "") or "").strip()

    # ------------------------------------------------------------------ chat

    def chat(self, messages: list, tools: list | None = None, options: dict | None = None,
             think=None, format=None) -> dict:
        """
        Multi-turn chat via /api/chat, with optional tool calling, thinking and
        schema-enforced output. Returns the assistant message: "content" holds
        text, "thinking" the reasoning trace (when the model exposes one), and
        "tool_calls" the functions the model wants run. The caller decides
        whether to run them and loop.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": self._options(options),
        }
        if tools:
            payload["tools"] = tools
        if format is not None:
            payload["format"] = format
        effective_think = self.think if think is None else think
        if effective_think is not None:
            payload["think"] = effective_think

        data = self._post("/api/chat", payload)
        message = data.get("message") or {}
        return {
            "role": message.get("role", "assistant"),
            "content": (message.get("content") or "").strip(),
            "thinking": (message.get("thinking") or "").strip(),
            "tool_calls": message.get("tool_calls") or [],
        }

    # ------------------------------------------------------------- generation

    def generate(self, prompt: str) -> str:
        """
        Default generate.
        Adds basic system injection.
        If prompt requests JSON, we attempt to enforce valid JSON by retrying.
        """
        wants_json = _looks_like_json_request(prompt)

        system = self.system_default

        if not wants_json:
            return self._post_generate(prompt=prompt, system=system, options=None)

        return self.generate_json(prompt)

    def generate_structured(self, prompt: str, schema: dict) -> str:
        """
        Schema-enforced JSON: the runtime constrains decoding to the schema, so
        the shape is guaranteed at the source instead of rescued afterwards.
        Falls back to generate_json when structured mode is switched off.
        Thinking models spend tokens before the JSON, so the budget is raised.
        """
        if not self.structured:
            return self.generate_json(prompt)

        reply = self.chat(
            [
                {"role": "system", "content": self.system_default + " Output must be a single JSON object. No extra text."},
                {"role": "user", "content": prompt},
            ],
            format=schema,
            options={"temperature": 0.0, "num_predict": max(self.num_predict, self.structured_max_tokens)},
        )
        return reply["content"]

    def generate_json(self, prompt: str) -> str:
        """
        Strict JSON mode:
        1) ask for JSON only
        2) if invalid JSON, retry with correction instruction
        3) if still invalid, try to extract first JSON object
        """
        system = self.system_default + " Output must be a single JSON object. No extra text."

        correction_suffix = "\n\nReturn ONLY a single valid JSON object. No markdown. No comments. No extra keys beyond what is requested."

        last_text = ""

        for attempt in range(self.json_retries + 1):
            enforced_prompt = prompt if attempt == 0 else (prompt + correction_suffix)

            text = self._post_generate(
                prompt=enforced_prompt,
                system=system,
                options={"temperature": 0.0}
            )
            last_text = text

            try:
                json.loads(text)
                return text
            except Exception:
                extracted = _extract_first_json_object(text)
                if extracted:
                    try:
                        json.loads(extracted)
                        return extracted
                    except Exception:
                        pass

        return last_text
