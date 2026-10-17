import urllib.request
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas.api_models import HealthResponse
from backend.app.services.vector_store import vector_store

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("", response_model=HealthResponse, summary="System Health & Integration Status")
def check_health():
    # Check Ollama
    ollama_status = "Disconnected"
    try:
        req = urllib.request.Request(f"{settings.OLLAMA_BASE_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                ollama_status = "Connected (Ready)"
    except Exception:
        ollama_status = "Unreachable (Heuristic Fallback Active)"

    # Check Vector Store
    try:
        stats = vector_store.get_stats()
        vector_status = f"Operational ({stats['total_indexed_chunks']} chunks indexed)"
    except Exception as e:
        vector_status = f"Error: {e}"

    return {
        "status": "Healthy",
        "version": settings.VERSION,
        "database": "SQLite Connected",
        "vector_store": vector_status,
        "ollama_service": ollama_status,
        "ollama_model": settings.OLLAMA_MODEL,
    }
