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

    async def list_models(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/tags", timeout=10.0
            )
            resp.raise_for_status()
            data = resp.json()
            THINKING_FAMILIES = {"qwen3", "qwen35"}
            return [
                {
                    "name": m["name"],
                    "size": m.get("details", {}).get("parameter_size", ""),
                    "thinks": m.get("details", {}).get("family", "") in THINKING_FAMILIES,
                }
                for m in data.get("models", [])
            ]

    async def generate_stream(
        self, prompt: str, system: str = "", model: str | None = None,
        think: bool = True,
    ) -> AsyncIterator[dict]:
        """Stream LLM response using Ollama /api/chat.

        Yields dicts: type='thinking' | 'response' | 'stats'.
        """
        model = model or self.llm_model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "think": think,
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    msg = data.get("message", {})
                    thinking = msg.get("thinking", "")
                    token = msg.get("content", "")
                    if thinking:
                        yield {"token": thinking, "type": "thinking"}
                    if token:
                        yield {"token": token, "type": "response"}
                    if data.get("done", False):
                        stats = {}
                        for key in (
                            "total_duration", "load_duration",
                            "prompt_eval_count", "prompt_eval_duration",
                            "eval_count", "eval_duration",
                        ):
                            if key in data:
                                stats[key] = data[key]
                        if stats:
                            yield {"type": "stats", "stats": stats}
                        return

    async def generate(
        self, prompt: str, system: str = "", model: str | None = None
    ) -> str:
        tokens = []
        async for chunk in self.generate_stream(prompt, system, model):
            if chunk["type"] == "response":
                tokens.append(chunk["token"])
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
