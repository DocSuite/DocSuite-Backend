from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.deps import DbSession, require_permission
from app.models.user import User
from app.schemas.analysis import AnalysisMode, AnalysisRead
from app.services.ai.analyzer_service import analyze_document
from app.services.db.audit_service import create_audit_event
from app.services.db.analysis_service import create_analysis
from app.services.storage.file_service import save_upload_file

router = APIRouter()

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
    saved_file = await save_upload_file(file)
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
