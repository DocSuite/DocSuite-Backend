import asyncio
import json
import re
from pathlib import Path
from collections.abc import Callable

from app.core.exceptions import DocSuiteException
from app.schemas.analysis import AnalysisCreate, AnalysisMode
from app.services.ai.openai_client import OpenAIClient
from app.utils.file_utils import DocumentElement, DocumentExtraction, extract_structured_document


PROMPT_BY_MODE = {
    AnalysisMode.general: "analyzer_general.txt",
    AnalysisMode.academic: "analyzer_academic.txt",
}
MAX_ANALYZER_INPUT_CHARS = 45_000
ANALYZER_HEAD_CHARS = 25_000
ANALYZER_TAIL_CHARS = 20_000
ANALYZER_CHUNK_CHARS = 9_000
ANALYZER_CHUNK_OVERLAP = 800
ANALYZER_CHUNK_DELAY_SECONDS = 4
MAX_VISUAL_ELEMENTS = 6
MAX_VISUAL_IMAGE_BYTES = 4 * 1024 * 1024

VISION_PROMPT = (
    "Eres un analizador visual de documentos academicos. "
    "Determina si la imagen, grafica, tabla visual o captura contiene informacion relevante para el estudio. "
    "Responde solo JSON valido con: "
    '{"relevant": true, "type": "chart|table|diagram|photo|screenshot|other", '
    '"description": "descripcion breve", "extracted_text": "texto visible si existe", '
    '"academic_value": "por que importa para el analisis o null"}'
)


def _load_prompt(mode: AnalysisMode) -> str:
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / PROMPT_BY_MODE[mode]
    return prompt_path.read_text(encoding="utf-8")


def _extract_json_object(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {
                "language": None,
                "document_type": "No detectado",
                "executive_summary": cleaned or "La IA no devolvio contenido estructurado.",
                "key_points": [],
                "main_sections": [],
                "important_data": [],
                "conclusions": [],
                "keywords": [],
            }
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return {
                "language": None,
                "document_type": "No detectado",
                "executive_summary": cleaned or "La IA no devolvio contenido estructurado.",
                "key_points": [],
                "main_sections": [],
                "important_data": [],
                "conclusions": [],
                "keywords": [],
            }

    if not isinstance(parsed, dict):
        raise DocSuiteException("La IA devolvio una estructura no valida", status_code=502)
    return parsed


def _build_user_prompt(filename: str, mode: AnalysisMode, extracted_text: str) -> str:
    return (
        f"Archivo: {filename}\n"
        f"Modo solicitado: {mode.value}\n\n"
        "Texto extraido del documento:\n"
        f"{extracted_text}"
    )


def _format_elements(elements: list[DocumentElement]) -> str:
    blocks: list[str] = []
    for index, element in enumerate(elements, start=1):
        source_parts = [f"elemento {index}", f"tipo {element.type}"]
        if element.page is not None:
            source_parts.append(f"pagina {element.page}")
        if element.section:
            source_parts.append(f"seccion {element.section}")
        for key, value in element.metadata.items():
            if value is not None:
                source_parts.append(f"{key} {value}")
        blocks.append(f"[Fuente: {' | '.join(source_parts)}]\n{element.content.strip()}")
    return "\n\n".join(blocks).strip()


async def _interpret_visual_elements(
    extraction: DocumentExtraction,
    progress_callback: Callable[[int, str], None] | None = None,
) -> DocumentExtraction:
    image_elements = [element for element in extraction.elements if element.type == "image"]
    for index, element in enumerate(image_elements, start=1):
        if not element.image_bytes:
            element.content = f"{element.content}\nInterpretacion visual omitida: no se pudo extraer la imagen."
            element.metadata["vision"] = "sin_datos"
        elif len(element.image_bytes) > MAX_VISUAL_IMAGE_BYTES:
            element.content = f"{element.content}\nInterpretacion visual omitida: imagen mayor a 4 MB."
            element.metadata["vision"] = "omitido_tamano"
        elif index > MAX_VISUAL_ELEMENTS:
            element.content = (
                f"{element.content}\n"
                f"Interpretacion visual omitida: se interpreta un maximo de {MAX_VISUAL_ELEMENTS} imagenes por documento."
            )
            element.metadata["vision"] = "omitido_limite"

    visual_elements = [
        element
        for element in image_elements
        if element.type == "image"
        and element.image_bytes
        and len(element.image_bytes) <= MAX_VISUAL_IMAGE_BYTES
    ][:MAX_VISUAL_ELEMENTS]

    if not visual_elements:
        return extraction

    for index, element in enumerate(visual_elements, start=1):
        if progress_callback is not None:
            progress_callback(10, f"Interpretando imagen {index} de {len(visual_elements)}")
        try:
            response = await OpenAIClient().generate_with_images(
                VISION_PROMPT,
                "Interpreta esta imagen del documento. Si es decorativa o no aporta al estudio, indicalo claramente.",
                [(element.image_bytes or b"", element.image_mime_type or "image/png")],
            )
            payload = _extract_json_object(response)
            relevant = payload.get("relevant")
            visual_type = payload.get("type") or "image"
            description = payload.get("description") or "Imagen detectada."
            extracted_text = payload.get("extracted_text")
            academic_value = payload.get("academic_value")
            element.type = "chart" if visual_type == "chart" else "image"
            element.content = (
                f"Interpretacion visual: {description}\n"
                f"Texto visible: {extracted_text or 'No se detecto texto visible.'}\n"
                f"Valor academico: {academic_value or 'No se identifico aporte academico directo.'}\n"
                f"Relevante para el estudio: {'si' if relevant else 'no'}"
            )
            element.metadata["vision"] = "interpretado"
        except DocSuiteException as exc:
            element.content = (
                f"{element.content}\n"
                f"Interpretacion visual no disponible: {exc.detail}"
            )
            element.metadata["vision"] = "fallido"

    extraction.text = _format_elements(extraction.elements)
    return extraction


def _limit_text_for_model(extracted_text: str) -> str:
    if len(extracted_text) <= MAX_ANALYZER_INPUT_CHARS:
        return extracted_text

    head = extracted_text[:ANALYZER_HEAD_CHARS]
    tail = extracted_text[-ANALYZER_TAIL_CHARS:]
    return (
        f"{head}\n\n"
        "[Contenido intermedio omitido automaticamente para respetar el limite de tokens. "
        "El texto completo queda guardado en el historial.]\n\n"
        f"{tail}"
    )


def split_text_into_chunks(text: str, max_chars: int = ANALYZER_CHUNK_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            paragraph_break = text.rfind("\n\n", start, end)
            if paragraph_break > start + max_chars // 2:
                end = paragraph_break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - ANALYZER_CHUNK_OVERLAP)
    return chunks


def _build_chunk_prompt(filename: str, mode: AnalysisMode, chunk: str, index: int, total: int) -> str:
    return (
        f"Archivo: {filename}\n"
        f"Modo solicitado: {mode.value}\n"
        f"Fragmento: {index} de {total}\n\n"
        "Analiza solo este fragmento. Devuelve JSON parcial compatible con la estructura solicitada. "
        "No inventes datos que no aparezcan en este fragmento.\n\n"
        f"{chunk}"
    )


def _build_consolidation_prompt(filename: str, mode: AnalysisMode, partial_results: list[dict]) -> str:
    return (
        f"Archivo: {filename}\n"
        f"Modo solicitado: {mode.value}\n\n"
        "Consolida estos analisis parciales en un unico JSON final siguiendo exactamente la estructura solicitada. "
        "Elimina duplicados, prioriza datos concretos y conserva poblacion, muestra, resultados y conclusiones cuando existan.\n\n"
        f"{json.dumps(partial_results, ensure_ascii=False)}"
    )


async def _analyze_chunks(
    filename: str,
    mode: AnalysisMode,
    extracted_text: str,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict:
    prompt = _load_prompt(mode)
    chunks = split_text_into_chunks(extracted_text)

    if len(chunks) == 1:
        if progress_callback is not None:
            progress_callback(35, "Analizando documento")
        response = await OpenAIClient().generate(prompt, _build_user_prompt(filename, mode, _limit_text_for_model(extracted_text)))
        return _extract_json_object(response)

    partial_results: list[dict] = []
    total = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        progress = 15 + int((index - 1) / total * 60)
        if progress_callback is not None:
            progress_callback(progress, f"Analizando fragmento {index} de {total}")
        if index > 1:
            await asyncio.sleep(ANALYZER_CHUNK_DELAY_SECONDS)
        response = await OpenAIClient().generate(prompt, _build_chunk_prompt(filename, mode, chunk, index, total))
        partial_results.append(_extract_json_object(response))

    if progress_callback is not None:
        progress_callback(82, "Consolidando analisis")
    response = await OpenAIClient().generate(prompt, _build_consolidation_prompt(filename, mode, partial_results))
    return _extract_json_object(response)


async def analyze_document(file_path: Path, filename: str, mode: AnalysisMode) -> AnalysisCreate:
    return await analyze_document_with_progress(file_path, filename, mode)


async def analyze_document_with_progress(
    file_path: Path,
    filename: str,
    mode: AnalysisMode,
    progress_callback: Callable[[int, str], None] | None = None,
) -> AnalysisCreate:
    if progress_callback is not None:
        progress_callback(8, "Extrayendo texto")
    extraction = extract_structured_document(file_path)
    extraction = await _interpret_visual_elements(extraction, progress_callback)
    extracted_text = extraction.text
    if not extracted_text.strip():
        raise DocSuiteException("No se pudo extraer texto del documento")

    result = await _analyze_chunks(filename, mode, extracted_text, progress_callback)
    result["mode"] = mode.value
    result["source_filename"] = filename

    return AnalysisCreate(
        filename=filename,
        mode=mode,
        extracted_text=extracted_text,
        result=json.dumps(result, ensure_ascii=False),
    )
