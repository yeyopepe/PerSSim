"""Logging de llamadas Ollama a fichero JSON compartido."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def get_next_log_path(base_log_path: str) -> str:
    """Genera la ruta del siguiente archivo de log con sufijo numérico.

    Ejemplo: si base_log_path es 'logs/test-ollama.json', retorna:
    - 'logs/test-ollama-0001.json' si no existen archivos
    - 'logs/test-ollama-0002.json' si existe -0001.json
    """
    path = Path(base_log_path)
    parent = path.parent
    stem = path.stem
    suffix = path.suffix

    parent.mkdir(parents=True, exist_ok=True)

    existing_files = list(parent.glob(f"{stem}-[0-9][0-9][0-9][0-9]{suffix}"))
    if not existing_files:
        next_num = 1
    else:
        numbers = []
        for f in existing_files:
            match = re.search(r'-(\d{4})' + re.escape(suffix) + r'$', f.name)
            if match:
                numbers.append(int(match.group(1)))
        next_num = max(numbers) + 1 if numbers else 1

    return str(parent / f"{stem}-{next_num:04d}{suffix}")


def _ensure_json_array_initialized(log_path: str) -> None:
    """Asegura que el archivo esté inicializado como array JSON."""
    path = Path(log_path)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def write_entry(log_path: str, entry: dict) -> None:
    _ensure_json_array_initialized(log_path)

    content = Path(log_path).read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = []

    data.append(entry)
    Path(log_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def log_request(
    log_path: str,
    who: str,
    host: str,
    model: str,
    system: str,
    messages: list[dict],
    temperature: float,
) -> None:
    write_entry(log_path, {
        "ts": datetime.now(timezone.utc).isoformat(),
        "who": who,
        "model": model,
        "direction": "request",
        "endpoint": f"POST {host}/api/chat",
        "temperature": temperature,
        "system": system,
        "messages": messages,
    })


def log_response(
    log_path: str,
    who: str,
    host: str,
    response: Optional[str],
    model: str = "unknown",
) -> None:
    write_entry(log_path, {
        "ts": datetime.now(timezone.utc).isoformat(),
        "who": who,
        "model": model,
        "direction": "response",
        "endpoint": f"POST {host}/api/chat",
        "content": response,
    })
