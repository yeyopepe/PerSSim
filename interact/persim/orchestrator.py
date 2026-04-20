"""Servidor FastAPI del orquestador (orchestrator.py).

Hub central del sistema PerSSim. Arranca con:

    python -m persim.orchestrator --session ./session.json

Responsabilidades:
- Recibir intervenciones de los personajes via POST /character_talk.
- Distribuir cada intervención a todos los personajes via POST /listen.
- Escribir el log de conversación en formato literario.
- Mostrar el diálogo en la TUI (Rich).
- Leer comandos del usuario por stdin (wait / continue / texto libre).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

from persim.models import (
    CharacterTalkRequest,
    CharacterTalkResponse,
    ListenRequest,
    NarrateRequest,
    NarrateResponse,
    OrchestratorContinueResponse,
    OrchestratorWaitResponse,
)
from persim.tui import TUI

logger = logging.getLogger(__name__)

# Timeout para llamadas a los personajes
_CHAR_TIMEOUT = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)

# ---------------------------------------------------------------------------
# Estado global del orquestador
# ---------------------------------------------------------------------------

class OrchestratorState:
    def __init__(self, session: dict) -> None:
        self.session_id: str = session["session_id"]
        self.log_path: Path = Path(session["log_path"])
        self.initial_situation: str = session.get("initial_situation", "")

        # Registro de personajes: {id: {host, port}}
        self.characters: dict[str, dict] = {
            c["id"]: {"host": c["host"], "port": c["port"]}
            for c in session.get("characters", [])
        }

        # Asegurar que el directorio de log existe
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_file = self.log_path.open("a", encoding="utf-8")

        self.sequence_id: int = 0
        self.is_paused: bool = False
        self.tui: TUI = TUI()

    def char_url(self, character_id: str) -> str:
        c = self.characters[character_id]
        return f"http://{c['host']}:{c['port']}"

    def log_entry(self, entry: dict) -> None:
        """Escribe una entrada en el log con formato literario.

        Formato:
            DD/MM/YYYY - HH.MM
            De <quien> a <destinatario>
            <mensaje>
            <línea en blanco>
        """
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

    def close(self) -> None:
        self._log_file.close()


_state: Optional[OrchestratorState] = None

# ---------------------------------------------------------------------------
# Comunicación con personajes
# ---------------------------------------------------------------------------

async def _post_listen_to_all(
    state: OrchestratorState,
    from_: Optional[str],
    to: list[str],
    message: str,
) -> int:
    """Distribuye un mensaje /listen a todos los personajes. Devuelve cuántos OK."""
    payload = {"from": from_, "to": to, "message": message}
    ok = 0
    async with httpx.AsyncClient(timeout=_CHAR_TIMEOUT) as client:
        tasks = []
        for char_id, _ in state.characters.items():
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


async def _post_control_to_all(
    state: OrchestratorState, endpoint: str
) -> list[str]:
    """Envía /wait o /continue a todos los personajes. Devuelve IDs OK."""
    ok_ids = []
    async with httpx.AsyncClient(timeout=_CHAR_TIMEOUT) as client:
        for char_id in state.characters:
            url = f"{state.char_url(char_id)}/{endpoint}"
            try:
                resp = await client.post(url, json={})
                resp.raise_for_status()
                ok_ids.append(char_id)
            except Exception as exc:
                logger.warning("Error enviando /%s a %s: %s", endpoint, char_id, exc)
    return ok_ids


# ---------------------------------------------------------------------------
# Loop de lectura de stdin (comandos del usuario)
# ---------------------------------------------------------------------------

async def _stdin_command_loop(state: OrchestratorState) -> None:
    """Procesa comandos escritos por el usuario en la terminal."""
    loop = asyncio.get_event_loop()
    state.tui.start_stdin_reader(loop)

    while True:
        line = await state.tui.get_next_input()

        if line == "__EOF__":
            state.tui.print_system("EOF en stdin. El orquestador sigue corriendo.")
            break

        if line.lower() == "wait":
            state.is_paused = True
            ok = await _post_control_to_all(state, "wait")
            state.tui.print_system(f"Pausados: {', '.join(ok) or 'ninguno'}")

        elif line.lower() == "continue":
            state.is_paused = False
            ok = await _post_control_to_all(state, "continue")
            state.tui.print_system(f"Reanudados: {', '.join(ok) or 'ninguno'}")

        else:
            # Narración libre del usuario
            state.tui.print_narrator(line)
            ts = datetime.now(timezone.utc).isoformat()
            state.log_entry({
                "ts": ts, "who": None, "to": [], "message": line, "type": "narration"
            })
            await _post_listen_to_all(state, from_=None, to=[], message=line)


# ---------------------------------------------------------------------------
# Factoría de la aplicación
# ---------------------------------------------------------------------------

def create_app(session: dict) -> FastAPI:
    global _state

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _state
        _state = OrchestratorState(session)
        char_ids = list(_state.characters.keys())

        _state.tui.print_banner(_state.session_id, char_ids)

        # Lanzar loop de stdin
        asyncio.create_task(_stdin_command_loop(_state), name="stdin_loop")

        logger.info("Orquestador listo. Sesión: %s", _state.session_id)
        yield

        _state.close()
        logger.info("Orquestador apagado.")

    app = FastAPI(title="PerSSim Orchestrator", version="0.1.0", lifespan=lifespan)

    # -----------------------------------------------------------------------
    # Endpoints
    # -----------------------------------------------------------------------

    @app.post("/character_talk", response_model=CharacterTalkResponse)
    async def character_talk(req: CharacterTalkRequest):
        """Un personaje notifica una intervención."""
        state = _state
        if not req.who:
            raise HTTPException(status_code=400, detail="who is required")

        # Si el sistema está pausado, descartar silenciosamente el mensaje
        if state.is_paused:
            logger.debug("[orchestrator] Mensaje de %s descartado: sistema pausado", req.who)
            return CharacterTalkResponse(
                timestamp=datetime.now(timezone.utc).isoformat(),
                sequence_id=state.sequence_id,
            )

        state.sequence_id += 1
        ts = datetime.now(timezone.utc).isoformat()

        # Escribir en log
        state.log_entry({
            "ts": ts,
            "seq": state.sequence_id,
            "who": req.who,
            "to": req.to,
            "message": req.message,
        })

        # Mostrar en TUI
        state.tui.print_turn(
            who=req.who,
            to=req.to,
            message=req.message,
            timestamp=datetime.fromisoformat(ts).strftime("%H:%M:%S"),
            sequence_id=state.sequence_id,
        )

        # Distribuir a todos los personajes
        asyncio.create_task(
            _post_listen_to_all(
                state,
                from_=req.who,
                to=req.to,
                message=req.message,
            ),
            name=f"listen_broadcast_{state.sequence_id}",
        )

        return CharacterTalkResponse(
            timestamp=ts,
            sequence_id=state.sequence_id,
        )

    @app.post("/wait", response_model=OrchestratorWaitResponse)
    async def wait():
        """Pausa todos los personajes."""
        state = _state
        state.is_paused = True
        ok = await _post_control_to_all(state, "wait")
        state.tui.print_system(f"Sistema pausado ({len(ok)} personajes)")
        return OrchestratorWaitResponse(status="paused", characters_paused=len(ok))

    @app.post("/continue", response_model=OrchestratorContinueResponse)
    async def do_continue():
        """Reanuda todos los personajes."""
        state = _state
        state.is_paused = False
        ok = await _post_control_to_all(state, "continue")
        state.tui.print_system(f"Sistema reanudado ({len(ok)} personajes)")
        return OrchestratorContinueResponse(status="resumed", characters_resumed=len(ok))

    @app.post("/narrate", response_model=NarrateResponse)
    async def narrate(req: NarrateRequest):
        """Envía una narración del narrador a todos los personajes."""
        state = _state
        ts = datetime.now(timezone.utc).isoformat()

        state.tui.print_narrator(req.message)
        state.log_entry({
            "ts": ts, "who": None, "to": [], "message": req.message, "type": "narration"
        })

        n = await _post_listen_to_all(state, from_=None, to=[], message=req.message)

        return NarrateResponse(
            timestamp=ts,
            characters_notified=n,
        )

    return app


# ---------------------------------------------------------------------------
# Punto de entrada CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Orquestador PerSSim")
    parser.add_argument("--session", required=True, help="Ruta al fichero session.json")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )

    session_path = Path(args.session)
    if not session_path.exists():
        raise SystemExit(f"Session no encontrada: {session_path}")

    session = json.loads(session_path.read_text(encoding="utf-8"))
    app = create_app(session)

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level=args.log_level.lower())


if __name__ == "__main__":
    main()
