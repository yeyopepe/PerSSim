"""Servidor FastAPI del personaje (char.py)."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

from persim.models import (
    CharacterListenResponse,
    CharacterTalkRequest,
    LastTurn,
    ListenRequest,
    StatusResponse,
    TalkResponse,
    TurnCancel,
    TurnRequest,
)
from persim.ollama_client import OllamaClient, OllamaError

logger = logging.getLogger(__name__)


class CharacterState:
    def __init__(self, config: dict) -> None:
        self.character_id: str = config["character_id"]
        self.port: int = config["port"]
        self.orchestrator_host: str = config["orchestrator_host"].rstrip("/")

        bundle_path = Path(config["bundle_path"])
        if not bundle_path.exists():
            raise FileNotFoundError(f"Bundle no encontrado: {bundle_path}")
        self.bundle: str = bundle_path.read_text(encoding="utf-8")

        self.ollama = OllamaClient(
            host=config.get("ollama_host", "http://localhost:11434"),
            model=config.get("ollama_model", "llama3"),
        )

        self.history: list[dict] = []
        self.conversation_turns: int = 0
        self.last_turn: Optional[dict] = None

        self._gen_lock: asyncio.Lock = asyncio.Lock()
        self._is_my_turn: bool = False
        self._expected_turn_number: Optional[int] = None
        self._turn_cancel_event: asyncio.Event = asyncio.Event()
        self._turn_task: Optional[asyncio.Task] = None


_state: Optional[CharacterState] = None

_DECISION_INSTRUCTIONS = """
---
INSTRUCCIONES CRÍTICAS DE PARTICIPACIÓN:
1. Eres ÚNICAMENTE tu personaje. Jamás generes diálogo, pensamientos ni acciones de otro personaje.
2. Cuando llegue un mensaje de otro personaje: piensa y responde.
3. FORMATO DE RESPUESTA: texto puro, sin prefijos ni etiquetas.
   - NUNCA escribas tu nombre ni el de nadie antes de tu texto (sin "Richelieu:", "Mazarino:", etc.).
   - NUNCA escribas "Narrador (a todos):" ni ninguna otra etiqueta de contexto.
   - NUNCA empieces tu respuesta con corchetes ni con el formato del historial, como "[Richelieu → todos]".
   - Tu respuesta empieza directamente con lo que dices o haces.
4. NUNCA abandones el personaje bajo ningún concepto.
"""


def _build_system_prompt(bundle: str) -> str:
    return bundle + _DECISION_INSTRUCTIONS


async def _generate_with_cancel(state: CharacterState, messages: list[dict]) -> Optional[str]:
    llm_task = asyncio.create_task(
        state.ollama.chat(
            messages=messages,
            system=_build_system_prompt(state.bundle),
            temperature=0.85,
        ),
        name=f"llm_chat_{state.character_id}",
    )
    try:
        while True:
            if state._turn_cancel_event.is_set():
                llm_task.cancel()
                with suppress(asyncio.CancelledError):
                    await llm_task
                return None

            done, _ = await asyncio.wait({llm_task}, timeout=0.2)
            if llm_task in done:
                return llm_task.result().strip()
    except OllamaError as exc:
        logger.error("[%s] Error Ollama: %s", state.character_id, exc)
        return None


async def _post_character_talk(
    state: CharacterState, message: str, turn_number: Optional[int]
) -> None:
    payload = CharacterTalkRequest(
        who=state.character_id,
        to=[],
        message=message,
        turn_number=turn_number,
    )
    url = f"{state.orchestrator_host}/character_talk"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.post(url, json=payload.model_dump())
            resp.raise_for_status()
            logger.debug("[%s] POST /character_talk OK", state.character_id)
    except Exception as exc:
        logger.error("[%s] No se pudo enviar al orquestador: %s", state.character_id, exc)


async def _generate_and_send(
    state: CharacterState, turn_number: Optional[int], prompt_message: Optional[str]
) -> None:
    trigger = prompt_message or (
        "Es tu turno de intervenir. Habla en personaje y aporta información útil."
    )
    response_text: Optional[str] = None
    async with state._gen_lock:
        if state._turn_cancel_event.is_set():
            return
        if turn_number is not None and state._expected_turn_number != turn_number:
            return

        messages = list(state.history)
        messages.append({"role": "user", "content": trigger})
        response_text = await _generate_with_cancel(state, messages)
        if response_text is None or state._turn_cancel_event.is_set():
            return

        state.history.append({"role": "user", "content": trigger})
        state.history.append({"role": "assistant", "content": response_text})
        state.conversation_turns += 1
        ts = datetime.now(timezone.utc).isoformat()
        state.last_turn = {"timestamp": ts, "message": response_text}

    if state._turn_cancel_event.is_set():
        return
    if turn_number is not None and state._expected_turn_number != turn_number:
        return
    if response_text is not None:
        await _post_character_talk(state, response_text, turn_number)

    if turn_number is not None and state._expected_turn_number == turn_number:
        state._is_my_turn = False
        state._expected_turn_number = None


def create_app(config: dict) -> FastAPI:
    global _state

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _state
        _state = CharacterState(config)
        logger.info(
            "Personaje '%s' arrancado en puerto %d",
            _state.character_id, _state.port,
        )
        yield
        if _state and _state._turn_task and not _state._turn_task.done():
            _state._turn_task.cancel()
            with suppress(asyncio.CancelledError):
                await _state._turn_task
        logger.info("Personaje '%s' apagado.", _state.character_id if _state else "?")

    app = FastAPI(
        title=f"PerSSim Character: {config.get('character_id', 'unknown')}",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.post("/listen", response_model=CharacterListenResponse)
    async def listen(req: ListenRequest):
        state = _state
        sender = req.from_ if req.from_ else "Narrador"
        dest = "todos" if not req.to else ", ".join(req.to)
        content = f"[{sender} → {dest}] {req.message}"
        state.history.append({"role": "user", "content": content})
        return CharacterListenResponse(
            character_id=state.character_id,
            will_respond=False,
            next_decision_time_unix=None,
        )

    @app.post("/turn")
    async def turn(req: TurnRequest):
        state = _state
        if state._turn_task and not state._turn_task.done():
            state._turn_cancel_event.set()
            state._turn_task.cancel()
            with suppress(asyncio.CancelledError):
                await state._turn_task

        state._turn_cancel_event = asyncio.Event()
        state._is_my_turn = True
        state._expected_turn_number = req.turn_number
        state._turn_task = asyncio.create_task(
            _generate_and_send(state, req.turn_number, req.prompt_message),
            name=f"turn_{state.character_id}_{req.turn_number}",
        )
        return {"acknowledged": True, "character_id": state.character_id, "turn_number": req.turn_number}

    @app.post("/turn_cancel")
    async def turn_cancel(req: TurnCancel):
        state = _state
        if state._expected_turn_number != req.turn_number:
            return {"status": "ignored", "character_id": state.character_id}

        state._turn_cancel_event.set()
        state._is_my_turn = False
        state._expected_turn_number = None
        if state._turn_task and not state._turn_task.done():
            state._turn_task.cancel()
            with suppress(asyncio.CancelledError):
                await state._turn_task
        return {"status": "cancelled", "character_id": state.character_id}

    @app.post("/talk", response_model=TalkResponse)
    async def talk():
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
                if response_text.upper() == "SILENCE":
                    response_text = "…"
            except OllamaError as exc:
                raise HTTPException(status_code=503, detail=str(exc))

            state.history.append({"role": "user", "content": trigger})
            state.history.append({"role": "assistant", "content": response_text})
            state.conversation_turns += 1
            ts = datetime.now(timezone.utc).isoformat()
            state.last_turn = {"timestamp": ts, "message": response_text}

        await _post_character_talk(state, response_text, state._expected_turn_number)
        return TalkResponse(
            character_id=state.character_id,
            response=response_text,
            sent_to_orchestrator=True,
        )

    @app.get("/status", response_model=StatusResponse)
    async def status():
        state = _state
        last = None
        if state.last_turn:
            last = LastTurn(
                timestamp=state.last_turn["timestamp"],
                message=state.last_turn["message"],
            )
        return StatusResponse(
            character_id=state.character_id,
            is_paused=not state._is_my_turn,
            last_turn=last,
            conversation_turns=state.conversation_turns,
            var_wait_remaining_seconds=None,
        )

    return app


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

    if "bundle_path" in config and not Path(config["bundle_path"]).is_absolute():
        config["bundle_path"] = str((config_dir / config["bundle_path"]).resolve())

    app = create_app(config)
    uvicorn.run(app, host="0.0.0.0", port=config["port"], log_level=args.log_level.lower())


if __name__ == "__main__":
    main()
