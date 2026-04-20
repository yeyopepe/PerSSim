"""Launcher de sesión PerSSim (persim-launch).

Lee session.json, arranca el orquestador y los personajes como subprocesos
independientes, espera a que todos los puertos estén listos y envía la
situación inicial.

Uso:
    persim-launch --session ./session.json
    persim-launch --session ./session.json --log-level DEBUG
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

logger = logging.getLogger(__name__)

# Tiempo máximo esperando a que un proceso esté listo
_HEALTH_TIMEOUT_S = 60
_HEALTH_POLL_S = 0.5

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

async def _wait_for_port(host: str, port: int, timeout: float = _HEALTH_TIMEOUT_S) -> bool:
    """Espera hasta que el servidor en host:port responda con HTTP 200 a GET /."""
    url = f"http://{host}:{port}/"
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

def _launch_orchestrator(session_path: str, port: int, log_level: str) -> subprocess.Popen:
    cmd = [
        sys.executable, "-m", "persim.orchestrator",
        "--session", session_path,
        "--port", str(port),
        "--log-level", log_level,
    ]
    logger.info("Arrancando orquestador: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


def _launch_character(config_path: str, log_level: str) -> subprocess.Popen:
    cmd = [
        sys.executable, "-m", "persim.char",
        "--config", config_path,
        "--log-level", log_level,
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
    session = json.loads(Path(session_path).read_text(encoding="utf-8"))

    session_id = session.get("session_id", "unknown")
    initial_situation = session.get("initial_situation", "")
    orchestrator_port = 5000  # por defecto; configurable en session si se quiere
    orchestrator_host = "localhost"

    characters = session.get("characters", [])

    processes: list[subprocess.Popen] = []

    try:
        # 1. Arrancar orquestador
        orch_proc = _launch_orchestrator(session_path, orchestrator_port, log_level)
        processes.append(orch_proc)

        # 2. Arrancar personajes
        for char in characters:
            config_path = char.get("config")
            if not config_path:
                logger.warning("Personaje %s sin config; omitiendo.", char.get("id"))
                continue
            proc = _launch_character(config_path, log_level)
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
    parser.add_argument("--session", required=True, help="Ruta al fichero session.json")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )

    asyncio.run(run(args.session, args.log_level))


if __name__ == "__main__":
    main()
