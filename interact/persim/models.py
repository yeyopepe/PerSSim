"""Modelos Pydantic compartidos entre orquestador y personajes."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Payloads de entrada
# ---------------------------------------------------------------------------

class CharacterTalkRequest(BaseModel):
    """Un personaje notifica al orquestador de una intervención."""
    who: str = Field(..., description="ID del personaje que interviene")
    to: list[str] = Field(default_factory=list, description="IDs destinatarios; vacío = todos")
    message: str = Field(..., description="Contenido de la intervención")
    turn_number: Optional[int] = Field(None, description="Número de turno al que responde")


class TurnRequest(BaseModel):
    turn_number: int
    deadline_unix: Optional[float] = None
    prompt_message: Optional[str] = None


class TurnCancel(BaseModel):
    turn_number: int
    reason: str


class ListenRequest(BaseModel):
    """El orquestador distribuye un mensaje a los personajes."""
    from_: Optional[str] = Field(None, alias="from", description="ID del emisor; null = narrador")
    to: list[str] = Field(default_factory=list, description="IDs destinatarios; vacío = todos")
    message: str = Field(..., description="Contenido del mensaje")

    model_config = {"populate_by_name": True}


class NarrateRequest(BaseModel):
    """El usuario envía una narración al orquestador."""
    message: str = Field(..., description="Contenido de la narración")


# ---------------------------------------------------------------------------
# Respuestas
# ---------------------------------------------------------------------------

class CharacterTalkResponse(BaseModel):
    status: str = "logged"
    timestamp: str
    sequence_id: int


class ListenResponse(BaseModel):
    acknowledged: bool = True
    character_id: str
    will_respond: bool
    decision_time_ms: int


class CharacterListenResponse(BaseModel):
    acknowledged: bool = True
    character_id: str
    will_respond: bool
    next_decision_time_unix: Optional[float]


class TalkResponse(BaseModel):
    character_id: str
    response: str
    sent_to_orchestrator: bool


class NarrateResponse(BaseModel):
    status: str = "narrated"
    timestamp: str
    characters_notified: int


class LastTurn(BaseModel):
    timestamp: str
    message: str


class StatusResponse(BaseModel):
    character_id: str
    is_paused: bool
    last_turn: Optional[LastTurn]
    conversation_turns: int
    var_wait_remaining_seconds: Optional[float]
