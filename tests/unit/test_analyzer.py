from pathlib import Path

import pytest

from app.schemas.analysis import AnalysisMode
from app.services.ai import analyzer_service


@pytest.mark.asyncio
async def test_analyze_document_txt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("contenido academico", encoding="utf-8")

    async def fake_generate(self, system_prompt: str, user_prompt: str) -> str:
        return "resultado"

    monkeypatch.setattr(analyzer_service.OpenAIClient, "generate", fake_generate)

    result = await analyzer_service.analyze_document(file_path, "sample.txt", AnalysisMode.general)

    assert result.filename == "sample.txt"
    assert result.extracted_text == "contenido academico"
    assert result.result == "resultado"
