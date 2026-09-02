import os
from openai import OpenAI
from src.core.base_provider import BaseProvider

class GPTProvider(BaseProvider):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self.client = OpenAI(api_key=api_key)

        model = os.getenv("JAI_GPT_MODEL")
        if not model:
            raise RuntimeError("JAI_GPT_MODEL is not set")

        self.model = model

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )
        return response.output_text
