"""Interfaz de terminal usando Rich.

Proporciona helpers para que el orquestador muestre la conversación
con formato y colores, y gestione la entrada del usuario.

Diseño:
- Cada intervención se imprime como una línea coloreada en la consola.
- El input del usuario se lee desde stdin en un thread aparte para no
  bloquear el loop asyncio.
- El color de cada personaje se asigna dinámicamente en orden de aparición.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# ---------------------------------------------------------------------------
# Paleta de colores por personaje (se asignan en orden de aparición)
# ---------------------------------------------------------------------------

_PALETTE = [
    "bold cyan",
    "bold magenta",
    "bold yellow",
    "bold green",
    "bold blue",
    "bold red",
    "bold white",
]

_NARRATOR_STYLE = "italic dim white"
_USER_STYLE = "bold orange1"
_TIMESTAMP_STYLE = "dim white"

# ---------------------------------------------------------------------------
# Consola Rich global
# ---------------------------------------------------------------------------

_theme = Theme(
    {
        "narrator": _NARRATOR_STYLE,
        "user_input": _USER_STYLE,
        "ts": _TIMESTAMP_STYLE,
    }
)

console = Console(theme=_theme, highlight=False)


class TUI:
    """Gestor de la interfaz de terminal para el orquestador."""

    def __init__(self) -> None:
        self._char_colors: dict[str, str] = {}
        self._color_idx: int = 0
        self._input_queue: asyncio.Queue[str] = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._reader_task: Optional[asyncio.Task] = None

    def _color_for(self, character_id: str) -> str:
        if character_id not in self._char_colors:
            self._char_colors[character_id] = _PALETTE[self._color_idx % len(_PALETTE)]
            self._color_idx += 1
        return self._char_colors[character_id]

    def print_banner(self, session_id: str, characters: list[str]) -> None:
        """Muestra el banner de inicio."""
        chars_str = " · ".join(characters)
        panel = Panel(
            f"[bold]Sesión:[/bold] {session_id}\n"
            f"[bold]Personajes:[/bold] {chars_str}\n\n"
            "[dim]Comandos: [bold]wait[/bold] | [bold]continue[/bold] | texto libre para narrar[/dim]",
            title="[bold cyan]PerSSim[/bold cyan]",
            border_style="cyan",
        )
        console.print(panel)

    def print_turn(
        self,
        who: str,
        to: list[str],
        message: str,
        timestamp: Optional[str] = None,
        sequence_id: Optional[int] = None,
    ) -> None:
        """Imprime una intervención de un personaje."""
        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        color = self._color_for(who)

        dest = "→ todos" if not to else f"→ {', '.join(to)}"

        line = Text()
        line.append(f"[{ts}] ", style=_TIMESTAMP_STYLE)
        if sequence_id is not None:
            line.append(f"#{sequence_id:03d} ", style=_TIMESTAMP_STYLE)
        line.append(f"{who.upper()} ", style=color)
        line.append(f"({dest}): ", style="dim white")
        line.append(message, style="white")

        console.print(line)

    def print_narrator(self, message: str) -> None:
        """Imprime una narración del usuario/narrador."""
        ts = datetime.now().strftime("%H:%M:%S")
        line = Text()
        line.append(f"[{ts}] ", style=_TIMESTAMP_STYLE)
        line.append("NARRADOR: ", style=_USER_STYLE)
        line.append(message, style=_NARRATOR_STYLE)
        console.print(line)

    def print_system(self, message: str, style: str = "dim cyan") -> None:
        """Imprime un mensaje de sistema (pausa, reanudación, errores…)."""
        console.print(f"[{style}]⚙  {message}[/{style}]")

    def print_error(self, message: str) -> None:
        self.print_system(f"ERROR: {message}", style="bold red")

    # -----------------------------------------------------------------------
    # Lectura de stdin
    # -----------------------------------------------------------------------

    def start_stdin_reader(self, loop: asyncio.AbstractEventLoop) -> None:
        """Lanza un thread que lee stdin y encola las líneas."""
        self._loop = loop
        self._reader_task = loop.run_in_executor(None, self._stdin_thread)

    def _stdin_thread(self) -> None:
        """Hilo bloqueante que lee stdin línea a línea."""
        console.print(
            "[dim]Listo. Escribe un comando o narración y pulsa Enter.[/dim]"
        )
        try:
            for line in sys.stdin:
                line = line.strip()
                if line and self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._input_queue.put(line), self._loop
                    )
        except (EOFError, KeyboardInterrupt):
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._input_queue.put("__EOF__"), self._loop
                )

    async def get_next_input(self) -> str:
        """Espera la siguiente línea de stdin. Devuelve '__EOF__' si se cerró."""
        return await self._input_queue.get()
