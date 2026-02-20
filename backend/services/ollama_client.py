import json
from collections.abc import AsyncIterator

import httpx

from config.settings import get_settings


class OllamaClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.ollama_base_url
        self.llm_model = settings.llm_model
        self.embedding_model = settings.embedding_model

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/tags", timeout=5.0
                )
                return resp.status_code == 200
        except httpx.ConnectError:
            return False

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/tags", timeout=10.0
            )
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]

    async def generate_stream(
        self, prompt: str, system: str = "", model: str | None = None
    ) -> AsyncIterator[str]:
        model = model or self.llm_model
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        return

    async def generate(
        self, prompt: str, system: str = "", model: str | None = None
    ) -> str:
        tokens = []
        async for token in self.generate_stream(prompt, system, model):
            tokens.append(token)
        return "".join(tokens)

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        model = model or self.embedding_model
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": text},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["embeddings"][0]

    async def embed_batch(
        self, texts: list[str], model: str | None = None
    ) -> list[list[float]]:
        model = model or self.embedding_model
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": texts},
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["embeddings"]
