import pytest

from app.services.ai import acta_service
from app.utils.acta_tasks import extract_tasks_from_markdown


@pytest.mark.asyncio
async def test_generate_acta(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_generate(self, system_prompt: str, user_prompt: str) -> str:
        return "acta generada"

    monkeypatch.setattr(acta_service.OpenAIClient, "generate", fake_generate)

    result = await acta_service.generate_acta("audio.wav", "texto transcrito", {"segments": []})

    assert result.filename == "audio.wav"
    assert result.result == "acta generada"


def test_extract_tasks_from_markdown() -> None:
    content = """
## Tareas (seguimiento del docente)

- [ ] Verificar la implementacion del grad cam.
- [x] Realizar prueba aleatoria.

## Observaciones
- Sin observaciones adicionales.
"""

    tasks = extract_tasks_from_markdown(content)

    assert [task.description for task in tasks] == [
        "Verificar la implementacion del grad cam.",
        "Realizar prueba aleatoria.",
    ]
    assert [task.done for task in tasks] == [False, True]
