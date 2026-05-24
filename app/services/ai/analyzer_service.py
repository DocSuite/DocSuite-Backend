from pathlib import Path

from app.schemas.analysis import AnalysisCreate, AnalysisMode
from app.services.ai.openai_client import OpenAIClient
from app.utils.file_utils import extract_text_from_document


PROMPT_BY_MODE = {
    AnalysisMode.general: "analyzer_general.txt",
    AnalysisMode.academic: "analyzer_academic.txt",
}


def _load_prompt(mode: AnalysisMode) -> str:
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / PROMPT_BY_MODE[mode]
    return prompt_path.read_text(encoding="utf-8")


async def analyze_document(file_path: Path, filename: str, mode: AnalysisMode) -> AnalysisCreate:
    extracted_text = extract_text_from_document(file_path)
    prompt = _load_prompt(mode)
    result = await OpenAIClient().generate(prompt, extracted_text)
    return AnalysisCreate(
        filename=filename,
        mode=mode,
        extracted_text=extracted_text,
        result=result,
    )
