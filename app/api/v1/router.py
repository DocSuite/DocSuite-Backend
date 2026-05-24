from fastapi import APIRouter

from app.api.v1.endpoints import acta, analyzer, auth, historial

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(analyzer.router, prefix="/documents", tags=["documents"])
api_router.include_router(acta.router, prefix="/meeting-minutes", tags=["meeting-minutes"])
api_router.include_router(historial.router, prefix="/history", tags=["history"])
