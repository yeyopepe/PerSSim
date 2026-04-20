"""Launcher de sesión PerSSim (perssim-launch).

Lee session.config.json, arranca el orquestador y los personajes como subprocesos
independientes, espera a que todos los puertos estén listos y envía la
situación inicial.

Uso:
    perssim-launch --session ./session.config.json
    perssim-launch --session ./session.config.json --log-level DEBUG
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

from perssim.ollama_debug import get_next_log_path

logger = logging.getLogger(__name__)

# Tiempo máximo esperando a que un proceso esté listo
_HEALTH_TIMEOUT_S = 60
_HEALTH_POLL_S = 0.5


def _validate_turn_order(session: dict) -> None:
    characters = session.get("characters", [])
    known_ids = {c.get("id") for c in characters}
    turn_order = session.get("turn_order")
    if not turn_order or not isinstance(turn_order, list):
        raise ValueError("session.config.json requiere 'turn_order' (lista no vacía).")
    invalid = [c for c in turn_order if c not in known_ids]
    if invalid:
        raise ValueError(f"turn_order contiene IDs no definidos en characters: {invalid}")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

async def _wait_for_port(host: str, port: int, timeout: float = _HEALTH_TIMEOUT_S) -> bool:
    """Espera hasta que el servidor en host:port responda con HTTP 200 a GET /status."""
    url = f"http://{host}:{port}/status"
    deadline = time.monotonic() + timeout
    async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as client:
        while time.monotonic() < deadline:
            try:
                resp = await client.get(url)
                if resp.status_code < 500:
                    return True
            except Exception:
                pass
            await asyncio.sleep(_HEALTH_POLL_S)
    return False


# ---------------------------------------------------------------------------
# Lanzar subprocesos
# ---------------------------------------------------------------------------

def _debug_args(ollama_debug: bool, ollama_debug_log: Optional[str]) -> list[str]:
    args: list[str] = []
    if ollama_debug:
        args.append("--ollama-debug")
    if ollama_debug_log:
        args.extend(["--ollama-debug-log", ollama_debug_log])
    return args


def _launch_orchestrator(
    session_path: str, port: int, log_level: str,
    log_path: Optional[str],
    ollama_debug: bool, ollama_debug_log: Optional[str],
) -> subprocess.Popen:
    cmd = [
        sys.executable, "-m", "perssim.orchestrator",
        "--session", session_path,
        "--port", str(port),
        "--log-level", log_level,
    ]
    if log_path:
        cmd.extend(["--log-path", log_path])
    cmd.extend(_debug_args(ollama_debug, ollama_debug_log))
    logger.info("Arrancando orquestador: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


def _launch_character(
    config_path: str, log_level: str,
    ollama_debug: bool, ollama_debug_log: Optional[str],
) -> subprocess.Popen:
    cmd = [
        sys.executable, "-m", "perssim.char",
        "--config", config_path,
        "--log-level", log_level,
        *_debug_args(ollama_debug, ollama_debug_log),
    ]
    logger.info("Arrancando personaje: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


# ---------------------------------------------------------------------------
# Enviar situación inicial
# ---------------------------------------------------------------------------

async def _send_initial_situation(
    orchestrator_host: str, orchestrator_port: int, situation: str
) -> None:
    """Envía la situación inicial al orquestador via POST /narrate."""
    url = f"http://{orchestrator_host}:{orchestrator_port}/narrate"
    payload = {"message": situation}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Situación inicial enviada.")
        except Exception as exc:
            logger.error("No se pudo enviar la situación inicial: %s", exc)


# ---------------------------------------------------------------------------
# Main async
# ---------------------------------------------------------------------------

async def run(session_path: str, log_level: str) -> None:
    session_file = Path(session_path).resolve()
    session_dir = session_file.parent
    session = json.loads(session_file.read_text(encoding="utf-8"))
    _validate_turn_order(session)

    session_id = session.get("session_id", "unknown")
    initial_situation = session.get("initial_situation", "")
    orchestrator_port = 5000  # por defecto; configurable en session si se quiere
    orchestrator_host = "localhost"

    log_path: Optional[str] = session.get("log_path")
    if log_path and not Path(log_path).is_absolute():
        log_path = str((session_dir / log_path).resolve())
    if log_path:
        log_path = get_next_log_path(log_path)
        logger.info("Session log: %s", log_path)

    ollama_debug: bool = session.get("ollama_debug", False)
    ollama_debug_log: Optional[str] = session.get("ollama_debug_log")
    if ollama_debug_log and not Path(ollama_debug_log).is_absolute():
        ollama_debug_log = str((session_dir / ollama_debug_log).resolve())

    if ollama_debug_log:
        ollama_debug_log = get_next_log_path(ollama_debug_log)
        logger.info("Ollama debug log: %s", ollama_debug_log)

    characters = session.get("characters", [])

    processes: list[subprocess.Popen] = []

    try:
        # 1. Arrancar orquestador
        orch_proc = _launch_orchestrator(
            str(session_file), orchestrator_port, log_level, log_path, ollama_debug, ollama_debug_log
        )
        processes.append(orch_proc)

        # 2. Arrancar personajes
        for char in characters:
            config_path = char.get("config")
            if config_path:
                # Resolver relativo al directorio del session.config.json
                config_path = str((session_dir / config_path).resolve())
            if not config_path:
                logger.warning("Personaje %s sin config; omitiendo.", char.get("id"))
                continue
            proc = _launch_character(config_path, log_level, ollama_debug, ollama_debug_log)
            processes.append(proc)

        # 3. Health checks
        logger.info("Esperando a que los servidores estén listos…")

        # Orquestador
        ok = await _wait_for_port(orchestrator_host, orchestrator_port)
        if not ok:
            raise RuntimeError(
                f"El orquestador no arrancó en {_HEALTH_TIMEOUT_S}s "
                f"(puerto {orchestrator_port})"
            )
        logger.info("Orquestador listo en puerto %d", orchestrator_port)

        # Personajes
        for char in characters:
            host = char.get("host", "localhost")
            port = char.get("port")
            char_id = char.get("id", "?")
            ok = await _wait_for_port(host, port)
            if not ok:
                raise RuntimeError(
                    f"El personaje '{char_id}' no arrancó en {_HEALTH_TIMEOUT_S}s "
                    f"(puerto {port})"
                )
            logger.info("Personaje '%s' listo en puerto %d", char_id, port)

        # 4. Enviar situación inicial
        if initial_situation:
            # Pequeña pausa para que los personajes carguen sus bundles
            await asyncio.sleep(1.0)
            await _send_initial_situation(orchestrator_host, orchestrator_port, initial_situation)

        logger.info(
            "Sesión '%s' arrancada. %d personaje(s) activos. "
            "El launcher termina; los procesos siguen corriendo.",
            session_id, len(characters),
        )

        # El launcher termina aquí; los subprocesos son independientes.
        # Si se quiere modo "esperar a que terminen", descomentar:
        # for p in processes:
        #     p.wait()

    except Exception as exc:
        logger.error("Error en el arranque: %s", exc)
        # Matar subprocesos al fallar
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Lanzador de sesión PerSSim")
    parser.add_argument("--session", required=True, help="Ruta al fichero session.config.json")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )

    asyncio.run(run(args.session, args.log_level))


if __name__ == "__main__":
    main()
