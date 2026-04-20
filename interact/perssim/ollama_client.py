"""Wrapper async sobre la API de Ollama.

Uso:
    from perssim.ollama_client import OllamaClient

    client = OllamaClient(host="http://localhost:11434", model="llama3")
    response = await client.chat(system="...", messages=[...])
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Timeout generoso para modelos lentos en local
_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)


class OllamaError(Exception):
    """Error de comunicación con Ollama."""


class OllamaClient:
    """Cliente async sin estado para la API de Ollama."""

    def __init__(self, host: str, model: str) -> None:
        self.host = host.rstrip("/")
        self.model = model

    async def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        temperature: float = 0.8,
        stream: bool = False,
    ) -> str:
        """Envía una conversación a Ollama y devuelve el texto generado.

        Args:
            messages:    Lista de dicts {"role": "user"|"assistant", "content": "..."}.
            system:      System prompt (se envía como primer mensaje si no está en messages).
            temperature: Temperatura de sampling.
            stream:      Si True, hace streaming (actualmente no soportado aquí).

        Returns:
            Texto generado como string.

        Raises:
            OllamaError: Si hay un problema de red o la API devuelve error.
        """
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        url = f"{self.host}/api/chat"
        logger.debug("POST %s model=%s msgs=%d", url, self.model, len(messages))

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise OllamaError(
                f"Ollama devolvió HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise OllamaError(f"Error de red al contactar Ollama ({self.host}): {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise OllamaError(f"Respuesta inesperada de Ollama: {exc}") from exc

    async def is_available(self) -> bool:
        """Comprueba si Ollama está accesible."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                resp = await client.get(f"{self.host}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
