from pathlib import Path

from app.core.exceptions import DocSuiteException


def extract_text_from_document(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _extract_pdf_text(file_path)
    if suffix == ".docx":
        return _extract_docx_text(file_path)
    raise DocSuiteException("Formato no soportado. Usa PDF, DOCX o TXT.")


def _extract_pdf_text(file_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocSuiteException("pypdf no esta instalado", status_code=503) from exc

    reader = PdfReader(str(file_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_docx_text(file_path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise DocSuiteException("python-docx no esta instalado", status_code=503) from exc

    document = Document(str(file_path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
