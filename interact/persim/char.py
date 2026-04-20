"""Servidor FastAPI del personaje (char.py).

Cada instancia representa un único personaje histórico. Se arranca con:

    python -m persim.char --config ./chars/richelieu.config.json

Endpoints:
    POST /listen    – recibe intervención/narración del orquestador
    POST /talk      – fuerza intervención inmediata
    POST /wait      – pausa el bucle var_wait
    POST /continue  – reanuda el bucle var_wait
    GET  /status    – estado actual del personaje
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from persim.models import (
    CharacterListenResponse,
    CharacterTalkRequest,
    LastTurn,
    ListenRequest,
    StatusResponse,
    TalkResponse,
    WaitResponse,
)
from persim.ollama_client import OllamaClient, OllamaError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Estado global del personaje (singleton por proceso)
# ---------------------------------------------------------------------------

class CharacterState:
    def __init__(self, config: dict) -> None:
        self.character_id: str = config["character_id"]
        self.port: int = config["port"]
        self.orchestrator_host: str = config["orchestrator_host"].rstrip("/")
        self.wait_min: float = float(config.get("wait_min_seconds", 30))
        self.wait_max: float = float(config.get("wait_max_seconds", 120))

        # Cargar Bundle.md como system prompt
        bundle_path = Path(config["bundle_path"])
        if not bundle_path.exists():
            raise FileNotFoundError(f"Bundle no encontrado: {bundle_path}")
        self.bundle: str = bundle_path.read_text(encoding="utf-8")

        # Cliente Ollama
        self.ollama = OllamaClient(
            host=config.get("ollama_host", "http://localhost:11434"),
            model=config.get("ollama_model", "llama3"),
        )

        # Historial de conversación (formato Ollama: role + content)
        self.history: list[dict] = []
        self.conversation_turns: int = 0
        self.last_turn: Optional[dict] = None  # {"timestamp": ..., "message": ...}

        # Control de pausa
        self.is_paused: bool = False
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()  # no pausado inicialmente

        # var_wait
        self._var_wait_task: Optional[asyncio.Task] = None
        self._var_wait_next: Optional[float] = None  # timestamp UNIX del próximo chequeo

        # Lock para serializar generaciones (evitar dos LLM calls simultáneas)
        self._gen_lock: asyncio.Lock = asyncio.Lock()


# Variable de módulo; se inicializa en lifespan
_state: Optional[CharacterState] = None


# ---------------------------------------------------------------------------
# Construcción del system prompt enriquecido con instrucciones de decisión
# ---------------------------------------------------------------------------

_DECISION_INSTRUCTIONS = """
---
INSTRUCCIONES DE PARTICIPACIÓN EN LA CONVERSACIÓN:
Estás participando en una conversación multi-personaje. Cuando se te pregunte si quieres intervenir,
puedes hablar o guardar silencio. Si decides NO intervenir en este momento no respondas ni digas nada.
Si decides intervenir, habla directamente en personaje sin ninguna indicación meta.
NUNCA te salgas de tu personaje, bajo ningún concepto.
"""


def _build_system_prompt(bundle: str) -> str:
    return bundle + _DECISION_INSTRUCTIONS


# ---------------------------------------------------------------------------
# Lógica central: decidir y (si procede) hablar
# ---------------------------------------------------------------------------

async def _decide_and_maybe_talk(state: CharacterState, trigger_context: str) -> bool:
    """Llama al LLM para decidir si el personaje habla.

    El modelo recibe el historial + un mensaje de contexto describiendo la
    situación. Si responde 'SILENCE' (insensible a mayúsculas/espacios), no
    interviene. Cualquier otra respuesta se envía al orquestador.

    Returns:
        True si el personaje intervino, False si guardó silencio.
    """
    if state.is_paused:
        return False

    async with state._gen_lock:
        # Construir mensajes para el LLM
        messages = list(state.history)
        messages.append({"role": "user", "content": trigger_context})

        try:
            response = await state.ollama.chat(
                messages=messages,
                system=_build_system_prompt(state.bundle),
                temperature=0.85,
            )
        except OllamaError as exc:
            logger.error("[%s] Error Ollama: %s", state.character_id, exc)
            return False

        response = response.strip()

        # ¿El personaje decidió callar?
        if response.upper() == "SILENCE":
            logger.debug("[%s] decide: SILENCE", state.character_id)
            return False

        # Interviene: añadir al historial y notificar al orquestador
        state.history.append({"role": "user", "content": trigger_context})
        state.history.append({"role": "assistant", "content": response})
        state.conversation_turns += 1
        ts = datetime.now(timezone.utc).isoformat()
        state.last_turn = {"timestamp": ts, "message": response}

        logger.info("[%s] interviene: %s…", state.character_id, response[:60])
        await _post_character_talk(state, response)
        return True


async def _post_character_talk(state: CharacterState, message: str) -> None:
    """Envía la intervención al orquestador via POST /character_talk."""
    payload = CharacterTalkRequest(
        who=state.character_id,
        to=[],
        message=message,
    )
    url = f"{state.orchestrator_host}/character_talk"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.post(url, json=payload.model_dump())
            resp.raise_for_status()
            logger.debug("[%s] POST /character_talk OK", state.character_id)
    except Exception as exc:
        logger.error("[%s] No se pudo enviar al orquestador: %s", state.character_id, exc)


# ---------------------------------------------------------------------------
# Bucle var_wait
# ---------------------------------------------------------------------------

async def _var_wait_loop(state: CharacterState) -> None:
    """Tarea asyncio que activa al personaje periódicamente."""
    logger.info("[%s] Bucle var_wait iniciado (%.0f–%.0fs)",
                state.character_id, state.wait_min, state.wait_max)
    while True:
        # Esperar a que no esté pausado
        await state._pause_event.wait()

        wait_time = random.uniform(state.wait_min, state.wait_max)
        state._var_wait_next = time.time() + wait_time
        logger.debug("[%s] var_wait: esperando %.1fs", state.character_id, wait_time)

        # Dormir en tramos pequeños para reaccionar a pausas
        deadline = time.monotonic() + wait_time
        while time.monotonic() < deadline:
            if state.is_paused:
                break
            remaining = deadline - time.monotonic()
            await asyncio.sleep(min(1.0, remaining))

        if state.is_paused:
            continue  # volver al inicio del bucle y esperar a _pause_event

        trigger = (
            "Ha pasado un tiempo en silencio. ¿Quieres decir algo ahora? "
            "Recuerda: si no tienes nada relevante que añadir, responde SILENCE."
        )
        await _decide_and_maybe_talk(state, trigger)


# ---------------------------------------------------------------------------
# Lifespan: arranque y apagado
# ---------------------------------------------------------------------------

def create_app(config: dict) -> FastAPI:
    """Factoría de la aplicación FastAPI para un personaje dado."""

    global _state

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _state
        _state = CharacterState(config)
        logger.info(
            "Personaje '%s' arrancado en puerto %d",
            _state.character_id, _state.port,
        )
        # Lanzar bucle var_wait como tarea de fondo
        _state._var_wait_task = asyncio.create_task(
            _var_wait_loop(_state), name=f"var_wait_{_state.character_id}"
        )
        yield
        # Apagado
        if _state._var_wait_task:
            _state._var_wait_task.cancel()
            try:
                await _state._var_wait_task
            except asyncio.CancelledError:
                pass
        logger.info("Personaje '%s' apagado.", _state.character_id)

    app = FastAPI(
        title=f"PerSSim Character: {config.get('character_id', 'unknown')}",
        version="0.1.0",
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------------
    # Endpoints
    # -----------------------------------------------------------------------

    @app.post("/listen", response_model=CharacterListenResponse)
    async def listen(req: ListenRequest):
        """Recibe un mensaje del orquestador y decide si intervenir."""
        t0 = time.monotonic()
        state = _state

        # ¿Va dirigido a este personaje?
        is_addressed = (not req.to) or (state.character_id in req.to)

        # Añadir al historial (siempre, aunque no sea el destinatario)
        sender = req.from_ if req.from_ else "Narrador"
        content = f"[{sender} → {'todos' if not req.to else ', '.join(req.to)}]: {req.message}"
        state.history.append({"role": "user", "content": content})

        will_respond = False
        if is_addressed and not state.is_paused:
            trigger = (
                f"{content}\n\n"
                "¿Quieres responder a esto ahora? "
                "Si no, responde SILENCE."
            )
            will_respond = await _decide_and_maybe_talk(state, trigger)

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        next_ts = state._var_wait_next

        return CharacterListenResponse(
            character_id=state.character_id,
            will_respond=will_respond,
            next_decision_time_unix=next_ts,
        )

    @app.post("/talk", response_model=TalkResponse)
    async def talk():
        """Fuerza una intervención inmediata, ignorando var_wait."""
        state = _state
        trigger = (
            "Se te pide que intervengas ahora. Habla en personaje. "
            "No uses SILENCE; di algo relevante para la situación actual."
        )
        response_text = ""
        async with state._gen_lock:
            messages = list(state.history)
            messages.append({"role": "user", "content": trigger})
            try:
                response_text = await state.ollama.chat(
                    messages=messages,
                    system=_build_system_prompt(state.bundle),
                    temperature=0.85,
                )
                response_text = response_text.strip()
                # Si aun así dice SILENCE, forzamos algo
                if response_text.upper() == "SILENCE":
                    response_text = "…"
            except OllamaError as exc:
                raise HTTPException(status_code=503, detail=str(exc))

            state.history.append({"role": "user", "content": trigger})
            state.history.append({"role": "assistant", "content": response_text})
            state.conversation_turns += 1
            ts = datetime.now(timezone.utc).isoformat()
            state.last_turn = {"timestamp": ts, "message": response_text}

        await _post_character_talk(state, response_text)

        return TalkResponse(
            character_id=state.character_id,
            response=response_text,
            sent_to_orchestrator=True,
        )

    @app.post("/wait", response_model=WaitResponse)
    async def wait():
        """Pausa el bucle var_wait."""
        state = _state
        state.is_paused = True
        state._pause_event.clear()
        logger.info("[%s] PAUSED", state.character_id)
        return WaitResponse(character_id=state.character_id, status="paused")

    @app.post("/continue", response_model=WaitResponse)
    async def do_continue():
        """Reanuda el bucle var_wait."""
        state = _state
        state.is_paused = False
        state._pause_event.set()
        logger.info("[%s] RESUMED", state.character_id)
        return WaitResponse(character_id=state.character_id, status="resumed")

    @app.get("/status", response_model=StatusResponse)
    async def status():
        """Estado actual del personaje."""
        state = _state
        remaining = None
        if state._var_wait_next is not None:
            remaining = max(0.0, state._var_wait_next - time.time())

        last = None
        if state.last_turn:
            last = LastTurn(
                timestamp=state.last_turn["timestamp"],
                message=state.last_turn["message"],
            )

        return StatusResponse(
            character_id=state.character_id,
            is_paused=state.is_paused,
            last_turn=last,
            conversation_turns=state.conversation_turns,
            var_wait_remaining_seconds=remaining,
        )

    return app


# ---------------------------------------------------------------------------
# Punto de entrada CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Servidor de personaje PerSSim")
    parser.add_argument("--config", required=True, help="Ruta al fichero char.config.json")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        raise SystemExit(f"Config no encontrada: {config_path}")

    config_dir = config_path.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))

    # Resolver rutas relativas al directorio del config
    if "bundle_path" in config and not Path(config["bundle_path"]).is_absolute():
        config["bundle_path"] = str((config_dir / config["bundle_path"]).resolve())

    app = create_app(config)

    uvicorn.run(app, host="0.0.0.0", port=config["port"], log_level=args.log_level.lower())


if __name__ == "__main__":
    main()
