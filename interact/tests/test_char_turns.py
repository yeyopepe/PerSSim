import asyncio
import time

from fastapi.testclient import TestClient

from perssim import char


def _config(tmp_path):
    bundle = tmp_path / "bundle.md"
    bundle.write_text("bundle", encoding="utf-8")
    return {
        "character_id": "richelieu",
        "bundle_path": str(bundle),
        "ollama_model": "llama3",
        "ollama_host": "http://localhost:11434",
        "orchestrator_host": "http://localhost:5000",
        "port": 5001,
    }


def test_turn_triggers_generation_and_post(monkeypatch, tmp_path):
    posts = []

    async def _fake_generate_with_cancel(state, messages):
        return "respuesta de turno"

    async def _fake_post_character_talk(state, message, turn_number):
        posts.append({"message": message, "turn_number": turn_number, "who": state.character_id})

    monkeypatch.setattr(char, "_generate_with_cancel", _fake_generate_with_cancel)
    monkeypatch.setattr(char, "_post_character_talk", _fake_post_character_talk)

    app = char.create_app(_config(tmp_path))
    with TestClient(app) as client:
        resp = client.post("/turn", json={"turn_number": 7, "deadline_unix": None, "prompt_message": None})
        assert resp.status_code == 200
        time.sleep(0.05)
        assert posts == [{"message": "respuesta de turno", "turn_number": 7, "who": "richelieu"}]


def test_turn_cancel_interrupts_generation(monkeypatch, tmp_path):
    posts = []

    async def _slow_generate_with_cancel(state, messages):
        await asyncio.sleep(0.5)
        return "respuesta tardía"

    async def _fake_post_character_talk(state, message, turn_number):
        posts.append({"message": message, "turn_number": turn_number, "who": state.character_id})

    monkeypatch.setattr(char, "_generate_with_cancel", _slow_generate_with_cancel)
    monkeypatch.setattr(char, "_post_character_talk", _fake_post_character_talk)

    app = char.create_app(_config(tmp_path))
    with TestClient(app) as client:
        resp = client.post("/turn", json={"turn_number": 3, "deadline_unix": None, "prompt_message": None})
        assert resp.status_code == 200
        cancel = client.post("/turn_cancel", json={"turn_number": 3, "reason": "timeout"})
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"
        time.sleep(0.1)
        assert posts == []
