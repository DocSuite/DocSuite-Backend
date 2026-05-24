from pathlib import Path

from app.schemas.acta import ActaCreate
from app.services.ai.openai_client import OpenAIClient


def _load_prompt() -> str:
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "acta_system.txt"
    return prompt_path.read_text(encoding="utf-8")


async def generate_acta(filename: str, transcription: str, diarization: dict | None) -> ActaCreate:
    diarization_text = "" if diarization is None else str(diarization)
    user_prompt = f"TRANSCRIPCION:\n{transcription}\n\nDIARIZACION:\n{diarization_text}"
    result = await OpenAIClient().generate(_load_prompt(), user_prompt)
    return ActaCreate(
        filename=filename,
        transcription=transcription,
        diarization=diarization,
        result=result,
        tasks=[],
    )
