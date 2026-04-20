import asyncio
import time

from fastapi.testclient import TestClient

from perssim import orchestrator


def _session(timeout: int = 30):
    return {
        "session_id": "test-session",
        "log_path": "/tmp/persim-test.log",
        "turn_order": ["a", "b"],
        "turn_timeout_seconds": timeout,
        "characters": [
            {"id": "a", "host": "localhost", "port": 5001},
            {"id": "b", "host": "localhost", "port": 5002},
        ],
    }


def test_notify_and_advance_on_response(monkeypatch):
    async def _noop_stdin(state):
        await asyncio.sleep(3600)

    calls = []

    async def _fake_post_with_retries(self, character_id, endpoint, payload, retries=3):
        calls.append((character_id, endpoint, payload))
        return True

    monkeypatch.setattr(orchestrator, "_stdin_command_loop", _noop_stdin)
    monkeypatch.setattr(orchestrator.OrchestratorState, "_post_with_retries", _fake_post_with_retries)

    app = orchestrator.create_app(_session())
    with TestClient(app) as client:
        time.sleep(0.05)
        assert any(c[0] == "a" and c[1] == "/turn" and c[2]["turn_number"] == 1 for c in calls)

        resp = client.post(
            "/character_talk",
            json={"who": "a", "to": [], "message": "hola", "turn_number": 1},
        )
        assert resp.status_code == 200
        assert any(c[0] == "b" and c[1] == "/turn" and c[2]["turn_number"] == 2 for c in calls)


def test_timeout_advances_and_sends_cancel(monkeypatch):
    async def _noop_stdin(state):
        await asyncio.sleep(3600)

    calls = []

    async def _fake_post_with_retries(self, character_id, endpoint, payload, retries=3):
        calls.append((character_id, endpoint, payload))
        return True

    monkeypatch.setattr(orchestrator, "_stdin_command_loop", _noop_stdin)
    monkeypatch.setattr(orchestrator.OrchestratorState, "_post_with_retries", _fake_post_with_retries)

    app = orchestrator.create_app(_session(timeout=1))
    with TestClient(app):
        time.sleep(1.3)
        assert any(c[0] == "a" and c[1] == "/turn_cancel" and c[2]["turn_number"] == 1 for c in calls)
        assert any(c[0] == "b" and c[1] == "/turn" and c[2]["turn_number"] == 2 for c in calls)


def test_out_of_turn_rejected(monkeypatch):
    async def _noop_stdin(state):
        await asyncio.sleep(3600)

    calls = []

    async def _fake_post_with_retries(self, character_id, endpoint, payload, retries=3):
        calls.append((character_id, endpoint, payload))
        return True

    monkeypatch.setattr(orchestrator, "_stdin_command_loop", _noop_stdin)
    monkeypatch.setattr(orchestrator.OrchestratorState, "_post_with_retries", _fake_post_with_retries)

    app = orchestrator.create_app(_session())
    with TestClient(app) as client:
        time.sleep(0.05)
        resp = client.post(
            "/character_talk",
            json={"who": "b", "to": [], "message": "fuera de turno", "turn_number": 1},
        )
        assert resp.status_code == 409
        assert sum(1 for c in calls if c[1] == "/turn") == 1
