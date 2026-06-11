from pathlib import Path
import json

import pytest

from app.schemas.analysis import AnalysisMode
from app.services.ai import analyzer_service


@pytest.mark.asyncio
async def test_analyze_document_txt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("contenido academico", encoding="utf-8")

    async def fake_generate(self, system_prompt: str, user_prompt: str) -> str:
        return '{"language":"es","document_type":"informe","executive_summary":"resultado"}'

    monkeypatch.setattr(analyzer_service.OpenAIClient, "generate", fake_generate)

    result = await analyzer_service.analyze_document(file_path, "sample.txt", AnalysisMode.general)

    assert result.filename == "sample.txt"
    assert "Fuente:" in result.extracted_text
    assert "contenido academico" in result.extracted_text
    payload = json.loads(result.result)
    assert payload["language"] == "es"
    assert payload["mode"] == "general"
    assert payload["source_filename"] == "sample.txt"


@pytest.mark.asyncio
async def test_analyze_document_md(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file_path = tmp_path / "sample.md"
    file_path.write_text("# Titulo\n\nContenido", encoding="utf-8")

    async def fake_generate(self, system_prompt: str, user_prompt: str) -> str:
        return '```json\n{"language":"es","document_type":"markdown"}\n```'

    monkeypatch.setattr(analyzer_service.OpenAIClient, "generate", fake_generate)

    result = await analyzer_service.analyze_document(file_path, "sample.md", AnalysisMode.general)
    payload = json.loads(result.result)

    assert "Fuente:" in result.extracted_text
    assert "# Titulo\n\nContenido" in result.extracted_text
    assert payload["document_type"] == "markdown"


@pytest.mark.asyncio
async def test_analyze_document_limits_model_input(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file_path = tmp_path / "large.txt"
    file_path.write_text("a" * 80_000, encoding="utf-8")
    captured_prompts: list[str] = []

    async def fake_generate(self, system_prompt: str, user_prompt: str) -> str:
        captured_prompts.append(user_prompt)
        return '{"language":"es","document_type":"paper"}'

    monkeypatch.setattr(analyzer_service.OpenAIClient, "generate", fake_generate)
    monkeypatch.setattr(analyzer_service, "ANALYZER_CHUNK_DELAY_SECONDS", 0)

    result = await analyzer_service.analyze_document(file_path, "large.txt", AnalysisMode.academic)

    assert len(captured_prompts) > 1
    assert all(len(prompt) < 50_000 for prompt in captured_prompts)
    assert "Fuente:" in result.extracted_text
