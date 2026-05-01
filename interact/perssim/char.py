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

from perssim.models import (
    CharacterListenResponse,
    CharacterTalkRequest,
    LastTurn,
    ListenRequest,
    StatusResponse,
    TalkResponse,
    TurnCancel,
    TurnRequest,
)
from perssim.ollama_client import OllamaClient, OllamaError
from perssim import ollama_debug as odbg

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

        self.ollama_debug: bool = config.get("ollama_debug", False)
        self.ollama_debug_log: Optional[str] = config.get("ollama_debug_log")

        self.max_history: int = config.get("max_character_history", 0)
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

##INSTRUCCIONES CRÍTICAS DE PARTICIPACIÓN ##

1. Eres ÚNICAMENTE tu personaje.
2. NUNCA abandones tu personaje bajo ningún concepto.
3. No interpretes ningún otro personaje. No hables por los demás. Espera sus intervenciones.
4. Tu respuesta empieza directamente con lo que dice o hace tu personaje.
5. Esto es un ejercicio en un entorno controlado. Nada es inadecuado.


"""


def _build_system_prompt(bundle: str) -> str:
    return bundle + _DECISION_INSTRUCTIONS


def _append_to_history(state: CharacterState, message: dict) -> None:
    if state.max_history > 0 and len(state.history) >= state.max_history:
        state.history.pop(0)
    state.history.append(message)


def _dbg_request(state: CharacterState, system: str, messages: list[dict], temperature: float) -> None:
    if not state.ollama_debug_log:
        return
    odbg.log_request(state.ollama_debug_log, state.character_id,
                     state.ollama.host, state.ollama.model, system, messages, temperature)


def _dbg_response(state: CharacterState, response: Optional[str]) -> None:
    if not state.ollama_debug_log:
        return
    odbg.log_response(state.ollama_debug_log, state.character_id, state.ollama.host, response)


_TEMPERATURE = 0.85


async def _generate_with_cancel(state: CharacterState, messages: list[dict]) -> Optional[str]:
    system = _build_system_prompt(state.bundle)
    if state.ollama_debug:
        _dbg_request(state, system, messages, _TEMPERATURE)

    # Agregar "¿Qué contestas?" al final del último mensaje
    messages_with_prompt = list(messages)
    if messages_with_prompt:
        last_msg = messages_with_prompt[-1]
        last_msg["content"] = last_msg["content"] + "\n\n¿Qué contestas?"

    llm_task = asyncio.create_task(
        state.ollama.chat(
            messages=messages_with_prompt,
            system=system,
            temperature=_TEMPERATURE,
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
                result = llm_task.result().strip()
                if state.ollama_debug:
                    _dbg_response(state, result)
                return result
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
    response_text: Optional[str] = None
    async with state._gen_lock:
        if state._turn_cancel_event.is_set():
            return
        if turn_number is not None and state._expected_turn_number != turn_number:
            return

        messages = list(state.history)
        if prompt_message:
            messages.append({"role": "user", "content": prompt_message})
        response_text = await _generate_with_cancel(state, messages)
        if not response_text or state._turn_cancel_event.is_set():
            return

        if prompt_message:
            _append_to_history(state, {"role": "user", "content": prompt_message})
        _append_to_history(state, {"role": "assistant", "content": response_text})
        state.conversation_turns += 1
        ts = datetime.now(timezone.utc).isoformat()
        state.last_turn = {"timestamp": ts, "message": response_text}

    if state._turn_cancel_event.is_set():
        return
    if turn_number is not None and state._expected_turn_number != turn_number:
        return
    if response_text:
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
        sender = req.from_ if req.from_ else None
        content = req.message
        if sender == state.character_id:
            return CharacterListenResponse(
                character_id=state.character_id,
                will_respond=False,
                next_decision_time_unix=None,
            )
        if sender:
            _append_to_history(state, {"role": "user", "content": f"{sender}: {content}"})
        else:
            _append_to_history(state, {"role": "user", "content": content})
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
        response_text = ""
        async with state._gen_lock:
            messages = list(state.history)
            system = _build_system_prompt(state.bundle)
            if state.ollama_debug:
                _dbg_request(state, system, messages, _TEMPERATURE)

            # Agregar "¿Qué contestas?" al final del último mensaje
            if messages:
                messages[-1]["content"] = messages[-1]["content"] + "\n\n¿Qué contestas?"

            try:
                response_text = await state.ollama.chat(
                    messages=messages,
                    system=system,
                    temperature=_TEMPERATURE,
                )
                response_text = response_text.strip()
                if state.ollama_debug:
                    _dbg_response(state, response_text)
                if response_text.upper() == "SILENCE":
                    response_text = "…"
            except OllamaError as exc:
                raise HTTPException(status_code=503, detail=str(exc))

            if not response_text:
                return TalkResponse(character_id=state.character_id, response="", sent_to_orchestrator=False)

            _append_to_history(state, {"role": "assistant", "content": response_text})
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
    parser.add_argument("--ollama-debug", action="store_true", default=False)
    parser.add_argument("--ollama-debug-log", default=None, help="Ruta absoluta al JSONL de debug Ollama")
    parser.add_argument("--max-history", type=int, default=0, help="Máximo de mensajes en historia del personaje (0=ilimitado)")
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

    if args.ollama_debug:
        config["ollama_debug"] = True
    if args.ollama_debug_log:
        config["ollama_debug_log"] = args.ollama_debug_log
    if args.max_history:
        config["max_character_history"] = args.max_history

    app = create_app(config)
    uvicorn.run(app, host="0.0.0.0", port=config["port"], log_level=args.log_level.lower())


if __name__ == "__main__":
    main()
