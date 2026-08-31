# pyrefly: ignore [missing-import]
from fastapi import APIRouter

# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
@router.get("/api/v1/health", summary="Health check API v1")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "healthy"})
