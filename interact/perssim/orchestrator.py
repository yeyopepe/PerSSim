"""Servidor FastAPI del orquestador (orchestrator.py)."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

from perssim.models import (
    CharacterTalkRequest,
    CharacterTalkResponse,
    ListenRequest,
    NarrateRequest,
    NarrateResponse,
    TurnCancel,
    TurnRequest,
)
from perssim.tui import TUI
from perssim import ollama_debug as odbg
from perssim.ollama_debug import get_next_log_path

logger = logging.getLogger(__name__)

_CHAR_TIMEOUT = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)


class OrchestratorState:
    def __init__(self, session: dict) -> None:
        self.session_id: str = session["session_id"]
        self.log_path: Path = Path(session["log_path"])
        self.characters: dict[str, dict] = {
            c["id"]: {
                "host": c["host"],
                "port": c["port"],
                "initial_situation": c.get("initial_situation", ""),
            }
            for c in session.get("characters", [])
        }
        self.turn_order: list[str] = session.get("turn_order", [])
        if not self.turn_order:
            raise ValueError("session.turn_order es obligatorio y no puede estar vacío")
        invalid = [c for c in self.turn_order if c not in self.characters]
        if invalid:
            raise ValueError(f"turn_order contiene personajes desconocidos: {invalid}")

        self.turn_timeout_seconds: int = int(session.get("turn_timeout_seconds", 30))
        if self.turn_timeout_seconds <= 0:
            raise ValueError("turn_timeout_seconds debe ser mayor que 0")

        self.current_turn_index: int = 0
        self.current_turn_number: int = 1
        self.current_deadline_unix: Optional[float] = None
        self._turn_lock: asyncio.Lock = asyncio.Lock()
        self._turn_task: Optional[asyncio.Task] = None

        self.ollama_debug: bool = session.get("ollama_debug", False)
        ollama_debug_log_base = session.get("ollama_debug_log")
        self.ollama_debug_log: Optional[str] = (
            get_next_log_path(ollama_debug_log_base) if ollama_debug_log_base else None
        )

        self.sequence_id: int = 0
        self._turns_started: bool = False
        self._paused: bool = False
        self.tui: TUI = TUI()
        self.unreachable_characters: set[str] = set()

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_file = self.log_path.open("a", encoding="utf-8")

    def char_url(self, character_id: str) -> str:
        c = self.characters[character_id]
        return f"http://{c['host']}:{c['port']}"

    def current_character(self) -> str:
        return self.turn_order[self.current_turn_index]

    def log_entry(self, entry: dict) -> None:
        ts = datetime.fromisoformat(entry["ts"]).astimezone()
        ts_str = ts.strftime("%d/%m/%Y - %H.%M")
        who = entry.get("who")
        to = entry.get("to", [])
        message = entry.get("message", "")
        sender = who.capitalize() if who else "Narrador"
        recipient = ", ".join(t.capitalize() for t in to) if to else "Todos"
        self._log_file.write(f"{ts_str}\n")
        self._log_file.write(f"De {sender} a {recipient}\n")
        self._log_file.write(f"{message}\n\n")
        self._log_file.flush()

    def log_event(self, event_type: str, message: str) -> None:
        pass

    def close(self) -> None:
        self._log_file.close()

    async def _post_with_retries(
        self,
        character_id: str,
        endpoint: str,
        payload: dict,
        retries: int = 3,
    ) -> bool:
        url = f"{self.char_url(character_id)}{endpoint}"
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=_CHAR_TIMEOUT) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                return True
            except Exception as exc:
                logger.warning(
                    "Error POST %s a %s (intento %d/%d): %s",
                    endpoint,
                    character_id,
                    attempt,
                    retries,
                    exc,
                )
                if attempt < retries:
                    await asyncio.sleep(0.3)
        return False

    async def _notify_turn(self, character_id: str) -> None:
        turn_number = self.current_turn_number
        deadline = time.time() + self.turn_timeout_seconds
        payload = TurnRequest(
            turn_number=turn_number,
            deadline_unix=deadline,
            prompt_message=None,
        ).model_dump()
        ok = await self._post_with_retries(character_id, "/turn", payload)
        if not ok:
            self.unreachable_characters.add(character_id)
            self.log_event(
                "TURN_SKIP_UNREACHABLE",
                f"{character_id} no alcanzable en turno {turn_number}",
            )
            await self._advance_turn(reason="unreachable")
            return

        self.current_deadline_unix = deadline
        self.log_event(
            "TURN_START",
            f"turn_number={turn_number}, character={character_id}, deadline={deadline:.3f}",
        )
        self._turn_task = asyncio.create_task(
            self._turn_timeout_wait(turn_number, character_id, deadline),
            name=f"turn_timeout_{turn_number}_{character_id}",
        )

    async def _turn_timeout_wait(
        self, turn_number: int, character_id: str, deadline_unix: float
    ) -> None:
        sleep_for = max(0.0, deadline_unix - time.time())
        await asyncio.sleep(sleep_for)
        async with self._turn_lock:
            if (
                self.current_turn_number != turn_number
                or self.current_character() != character_id
                or self.current_deadline_unix != deadline_unix
            ):
                return
        await self._on_turn_timeout(turn_number, character_id)

    async def _on_turn_timeout(self, turn_number: int, character_id: str) -> None:
        self.log_event("TURN_TIMEOUT", f"turn_number={turn_number}, character={character_id}")
        cancel_payload = TurnCancel(turn_number=turn_number, reason="timeout").model_dump()
        await self._post_with_retries(character_id, "/turn_cancel", cancel_payload, retries=1)
        await self._advance_turn(reason="timeout")

    async def _advance_turn(self, reason: str, force_to: Optional[str] = None) -> dict:
        async with self._turn_lock:
            previous_turn = self.current_turn_number
            previous_character = self.current_character()

            if self._turn_task and not self._turn_task.done():
                self._turn_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._turn_task
            self._turn_task = None
            self.current_deadline_unix = None
            self.log_event(
                "TURN_END",
                f"turn_number={previous_turn}, character={previous_character}, reason={reason}",
            )

            if force_to is not None:
                if force_to not in self.turn_order:
                    raise HTTPException(status_code=404, detail=f"character desconocido: {force_to}")
                self.current_turn_index = self.turn_order.index(force_to)
            else:
                self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)

            self.current_turn_number += 1
            next_character = self.current_character()
            next_turn = self.current_turn_number

        if not self._paused or force_to is not None:
            await self._notify_turn(next_character)
        else:
            self.log_event("TURN_PAUSED", f"turn_number={next_turn}, character={next_character}")
        return {"next_character": next_character, "turn_number": next_turn}


_state: Optional[OrchestratorState] = None


async def _post_listen_to_all(
    state: OrchestratorState,
    from_: Optional[str],
    to: list[str],
    message: str,
) -> int:
    payload = ListenRequest(from_=from_, to=to, message=message).model_dump(by_alias=True)
    ok = 0
    async with httpx.AsyncClient(timeout=_CHAR_TIMEOUT) as client:
        tasks = []
        for char_id in state.characters:
            url = f"{state.char_url(char_id)}/listen"
            tasks.append(_post_listen_one(client, char_id, url, payload))
        results = await asyncio.gather(*tasks, return_exceptions=True)
    for char_id, result in zip(state.characters.keys(), results):
        if isinstance(result, Exception):
            logger.warning("Error notificando a %s: %s", char_id, result)
        else:
            ok += 1
    return ok


async def _post_listen_one(
    client: httpx.AsyncClient, char_id: str, url: str, payload: dict
) -> None:
    resp = await client.post(url, json=payload)
    resp.raise_for_status()
    logger.debug("POST /listen → %s: OK", char_id)


async def _stdin_command_loop(state: OrchestratorState) -> None:
    loop = asyncio.get_event_loop()
    state.tui.start_stdin_reader(loop)

    while True:
        line = await state.tui.get_next_input()
        if line == "__EOF__":
            state.tui.print_system("EOF en stdin. El orquestador sigue corriendo.")
            break

        if line.startswith("/"):
            parts = line[1:].split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].lower() if len(parts) > 1 else None
            if cmd == "next":
                result = await state._advance_turn(reason="forced", force_to=arg)
                state.tui.print_system(
                    f"Siguiente turno: {result['next_character']} (#{result['turn_number']})"
                )
            elif cmd == "turn-status":
                current = state.current_character()
                paused_str = " [PAUSADO]" if state._paused else ""
                state.tui.print_system(
                    f"turn={state.current_turn_number} current={current} "
                    f"order={state.turn_order} deadline={state.current_deadline_unix}{paused_str}"
                )
            elif cmd == "wait":
                state._paused = True
                state.log_event("SESSION_PAUSED", "usuario pausó la sesión")
                state.tui.print_system("Sesión pausada. Los turnos se detendrán al terminar el actual.")
            elif cmd == "continue":
                if state._paused:
                    state._paused = False
                    state.log_event("SESSION_RESUMED", "usuario reanudó la sesión")
                    state.tui.print_system("Sesión reanudada.")
                    await state._notify_turn(state.current_character())
                else:
                    state.tui.print_system("La sesión no estaba pausada.")
            else:
                state.tui.print_system(f"Comando desconocido: /{cmd}", style="bold red")
        else:
            state.tui.print_narrator(line)
            ts = datetime.now(timezone.utc).isoformat()
            state.log_entry({"ts": ts, "who": None, "to": [], "message": line, "type": "narration"})
            await _post_listen_to_all(state, from_=None, to=[], message=line)


def create_app(session: dict) -> FastAPI:
    global _state

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _state
        _state = OrchestratorState(session)
        _state.tui.print_banner(_state.session_id, list(_state.characters.keys()))
        asyncio.create_task(_stdin_command_loop(_state), name="stdin_loop")
        has_initial_situations = any(
            info.get("initial_situation") for info in _state.characters.values()
        )
        if not has_initial_situations:
            _state._turns_started = True
            asyncio.create_task(_state._notify_turn(_state.current_character()), name="turn_bootstrap")
        logger.info("Orquestador listo. Sesión: %s", _state.session_id)
        yield
        if _state._turn_task and not _state._turn_task.done():
            _state._turn_task.cancel()
            with suppress(asyncio.CancelledError):
                await _state._turn_task
        _state.close()
        logger.info("Orquestador apagado.")

    app = FastAPI(title="PerSSim Orchestrator", version="0.1.0", lifespan=lifespan)

    @app.post("/character_talk", response_model=CharacterTalkResponse)
    async def character_talk(req: CharacterTalkRequest):
        state = _state
        if not req.who:
            raise HTTPException(status_code=400, detail="who is required")

        async with state._turn_lock:
            current_character = state.current_character()
            expected_turn_number = state.current_turn_number
            if req.who != current_character:
                state.log_event(
                    "OUT_OF_TURN_ATTEMPT",
                    f"speaker={req.who}, expected={current_character}, turn={expected_turn_number}",
                )
                raise HTTPException(status_code=409, detail="out_of_turn")

            if req.turn_number is not None and req.turn_number != expected_turn_number:
                state.log_event(
                    "OUT_OF_TURN_ATTEMPT",
                    f"speaker={req.who}, turn={req.turn_number}, expected_turn={expected_turn_number}",
                )
                raise HTTPException(status_code=409, detail="turn_number_mismatch")

            if state._turn_task and not state._turn_task.done():
                state._turn_task.cancel()
                with suppress(asyncio.CancelledError):
                    await state._turn_task
            state._turn_task = None
            state.current_deadline_unix = None

            state.sequence_id += 1
            ts = datetime.now(timezone.utc).isoformat()
            state.log_entry(
                {
                    "ts": ts,
                    "seq": state.sequence_id,
                    "who": req.who,
                    "to": req.to,
                    "message": req.message,
                }
            )
            state.tui.print_turn(
                who=req.who,
                to=req.to,
                message=req.message,
                timestamp=datetime.fromisoformat(ts).strftime("%H:%M:%S"),
                sequence_id=state.sequence_id,
            )
        asyncio.create_task(
            _post_listen_to_all(state, from_=req.who, to=req.to, message=req.message),
            name=f"listen_broadcast_{state.sequence_id}",
        )
        await state._advance_turn(reason="responded")
        return CharacterTalkResponse(timestamp=ts, sequence_id=state.sequence_id)

    @app.post("/next")
    async def next_turn(payload: Optional[dict] = None):
        state = _state
        force_to = None
        if payload:
            force_to = payload.get("force_to")
        result = await state._advance_turn(reason="forced", force_to=force_to)
        return result

    @app.get("/turn_status")
    async def turn_status():
        state = _state
        return {
            "turn_order": state.turn_order,
            "current_character": state.current_character(),
            "turn_number": state.current_turn_number,
            "deadline_unix": state.current_deadline_unix,
        }

    @app.post("/start_turns")
    async def start_turns():
        state = _state
        if not state._turns_started:
            state._turns_started = True
            asyncio.create_task(
                state._notify_turn(state.current_character()), name="turn_bootstrap"
            )
        return {"status": "started", "turn_number": state.current_turn_number}

    @app.post("/narrate", response_model=NarrateResponse)
    async def narrate(req: NarrateRequest):
        state = _state
        ts = datetime.now(timezone.utc).isoformat()
        state.tui.print_narrator(req.message)
        state.log_entry({"ts": ts, "who": None, "to": [], "message": req.message, "type": "narration"})
        n = await _post_listen_to_all(state, from_=None, to=[], message=req.message)
        if not state._turns_started:
            state._turns_started = True
            asyncio.create_task(_state._notify_turn(state.current_character()), name="turn_bootstrap")
        return NarrateResponse(timestamp=ts, characters_notified=n)

    return app


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Orquestador PerSSim")
    parser.add_argument("--session", required=True, help="Ruta al fichero session.json")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--log-path", default=None, help="Ruta al fichero de log de sesión")
    parser.add_argument("--ollama-debug", action="store_true", default=False)
    parser.add_argument("--ollama-debug-log", default=None, help="Ruta absoluta al JSONL de debug Ollama")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )

    session_path = Path(args.session).resolve()
    if not session_path.exists():
        raise SystemExit(f"Session no encontrada: {session_path}")

    session_dir = session_path.parent
    session = json.loads(session_path.read_text(encoding="utf-8"))

    if "log_path" in session and not Path(session["log_path"]).is_absolute():
        session["log_path"] = str((session_dir / session["log_path"]).resolve())

    if args.log_path:
        session["log_path"] = args.log_path

    if args.ollama_debug:
        session["ollama_debug"] = True
    if args.ollama_debug_log:
        session["ollama_debug_log"] = args.ollama_debug_log

    if session.get("log_path"):
        log_path = session["log_path"]
        if not Path(log_path).is_absolute():
            log_path = str((session_dir / log_path).resolve())

        import re
        if not re.search(r'-\d{4}\.\w+$', log_path):
            log_path = get_next_log_path(log_path)

        session["log_path"] = log_path
        logger.info("Session log: %s", session["log_path"])

    if session.get("ollama_debug_log"):
        ollama_log_path = session["ollama_debug_log"]
        if not Path(ollama_log_path).is_absolute():
            ollama_log_path = str((session_dir / ollama_log_path).resolve())

        if not re.search(r'-\d{4}\.\w+$', ollama_log_path):
            ollama_log_path = get_next_log_path(ollama_log_path)

        session["ollama_debug_log"] = ollama_log_path
        logger.info("Ollama debug log: %s", session["ollama_debug_log"])

    app = create_app(session)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level=args.log_level.lower())


if __name__ == "__main__":
    main()
