import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


class LLMClient:
    """
    OpenAI-compatible LLM client.

    We use the OpenAI Python package as an interface, but the actual provider
    is controlled by OPENAI_BASE_URL in .env, for example Berget AI.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        env_path = Path.cwd() / ".env"
        load_dotenv(dotenv_path=env_path)

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model_name = model_name or os.getenv(
            "MODEL_NAME",
            "meta-llama/Llama-3.1-8B-Instruct"
        )

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Add it to .env or export it in the shell."
            )

        client_kwargs = {"api_key": self.api_key}

        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = OpenAI(**client_kwargs)

    def chat_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content
