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


class OllamaProvider(BaseProvider):

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or os.getenv("JAI_OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("JAI_OLLAMA_MODEL", "llama3")

        self.timeout_seconds = int(os.getenv("JAI_OLLAMA_TIMEOUT", "120"))
        self.temperature = float(os.getenv("JAI_TEMPERATURE", "0.2"))
        self.num_predict = int(os.getenv("JAI_MAX_TOKENS", "512"))

        self.json_retries = int(os.getenv("JAI_JSON_RETRIES", "2"))

        self.system_default = os.getenv(
            "JAI_SYSTEM_DEFAULT",
            "You are J_AI. Be precise. If asked for JSON, output only JSON."
        )

    def _post_generate(self, prompt: str, system: str | None, options: dict | None) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if system:
            payload["system"] = system

        final_options = {
            "temperature": self.temperature,
            "num_predict": self.num_predict
        }

        if options:
            final_options.update(options)

        payload["options"] = final_options

        response = requests.post(url, json=payload, timeout=self.timeout_seconds)

        if response.status_code != 200:
            raise RuntimeError(f"Ollama error {response.status_code}: {response.text}")

        data = response.json()
        return (data.get("response", "") or "").strip()

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
