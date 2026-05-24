import pytest

from app.services.ai import acta_service


@pytest.mark.asyncio
async def test_generate_acta(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_generate(self, system_prompt: str, user_prompt: str) -> str:
        return "acta generada"

    monkeypatch.setattr(acta_service.OpenAIClient, "generate", fake_generate)

    result = await acta_service.generate_acta("audio.wav", "texto transcrito", {"segments": []})

    assert result.filename == "audio.wav"
    assert result.result == "acta generada"
