import asyncio
import json
import urllib.parse
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession, require_permission
from app.core.exceptions import DocSuiteException
from app.models.user import User
from app.schemas.analysis import AnalysisJobRead, AnalysisMode, AnalysisRead
from app.services.ai.analyzer_job_service import create_analyzer_job, get_analyzer_job
from app.services.ai.analyzer_service import analyze_document
from app.services.db.audit_service import create_audit_event
from app.services.db.analysis_service import create_analysis, get_analysis_by_id
from app.services.export.docx_service import analyzer_to_docx
from app.services.storage.file_service import save_upload_file

router = APIRouter()
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

DocAnalyzerReader = Annotated[User, Depends(require_permission("/doc-analyzer"))]
DocAnalyzerCreator = Annotated[User, Depends(require_permission("/doc-analyzer", "create"))]
DocumentFile = Annotated[UploadFile, File()]
AnalysisModeForm = Annotated[AnalysisMode, Form()]


@router.post("/analysis", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
async def create_document_analysis(
    db: DbSession,
    current_user: DocAnalyzerCreator,
    file: DocumentFile,
    mode: AnalysisModeForm = AnalysisMode.general,
) -> AnalysisRead:
    saved_file = await save_upload_file(file, allowed_extensions=ALLOWED_DOCUMENT_EXTENSIONS)
    analysis_payload = await analyze_document(saved_file, file.filename or saved_file.name, mode)
    analysis = create_analysis(db, current_user.id, analysis_payload)
    create_audit_event(
        db,
        current_user.id,
        "Documento analizado",
        "DocAnalyzer",
        detail=analysis.filename,
        resource_id=analysis.id,
    )
    return AnalysisRead.model_validate(analysis)


@router.post("/analysis/jobs", response_model=AnalysisJobRead, status_code=status.HTTP_202_ACCEPTED)
async def create_document_analysis_job(
    current_user: DocAnalyzerCreator,
    file: DocumentFile,
    mode: AnalysisModeForm = AnalysisMode.general,
) -> AnalysisJobRead:
    saved_file = await save_upload_file(file, allowed_extensions=ALLOWED_DOCUMENT_EXTENSIONS)
    try:
        return create_analyzer_job(current_user.id, file.filename or saved_file.name, saved_file, mode)
    except RuntimeError as exc:
        raise DocSuiteException(str(exc), status_code=status.HTTP_429_TOO_MANY_REQUESTS) from exc


@router.get("/analysis/jobs/{job_id}", response_model=AnalysisJobRead)
def read_document_analysis_job(
    job_id: str,
    current_user: DocAnalyzerReader,
) -> AnalysisJobRead:
    job = get_analyzer_job(job_id, current_user.id)
    if job is None:
        raise DocSuiteException("Job no encontrado", status_code=status.HTTP_404_NOT_FOUND)
    return job


@router.get("/analysis/jobs/{job_id}/stream")
async def stream_document_analysis_job(
    job_id: str,
    current_user: DocAnalyzerReader,
) -> StreamingResponse:
    user_id = current_user.id

    async def _generator() -> AsyncGenerator[str, None]:
        while True:
            job = get_analyzer_job(job_id, user_id)
            if job is None:
                yield f"data: {json.dumps({'error': 'Job no encontrado'})}\n\n"
                break

            payload = {
                "progress": job.progress,
                "status": job.status,
                "message": job.message,
                "analysis_id": job.analysis_id,
                "error": job.error,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if job.status in ("completed", "failed"):
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/analysis/{analysis_id}", response_model=AnalysisRead)
def read_document_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: DocAnalyzerReader,
) -> AnalysisRead:
    analysis = get_analysis_by_id(db, analysis_id, current_user.id)
    if analysis is None:
        raise DocSuiteException("Analisis no encontrado", status_code=status.HTTP_404_NOT_FOUND)
    return AnalysisRead.model_validate(analysis)


@router.get("/analysis/{analysis_id}/export/docx")
def export_document_analysis_docx(
    analysis_id: str,
    db: DbSession,
    current_user: DocAnalyzerReader,
) -> StreamingResponse:
    analysis = get_analysis_by_id(db, analysis_id, current_user.id)
    if analysis is None:
        raise DocSuiteException("Analisis no encontrado", status_code=status.HTTP_404_NOT_FOUND)

    create_audit_event(
        db,
        current_user.id,
        "Exportacion DOCX",
        "DocAnalyzer",
        detail=analysis.filename,
        resource_id=analysis.id,
    )
    buf = analyzer_to_docx(analysis.filename, analysis.mode, analysis.result, analysis.extracted_text)
    safe_name = urllib.parse.quote(analysis.filename.rsplit(".", 1)[0] + "_analisis.docx")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
    )
