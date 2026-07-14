from fastapi import APIRouter, Depends, HTTPException

from backend.models.schemas import SyncResult
from backend.services import storage
from backend.services.auth import require_auth
from backend.services.sync_pipeline import purge_disallowed_articles, sync_all_keywords

router = APIRouter(prefix="/api", tags=["sync"], dependencies=[Depends(require_auth)])


@router.post("/sync", response_model=SyncResult)
def trigger_sync():
    try:
        return sync_all_keywords()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/purge-disallowed-articles")
def trigger_purge():
    """backend/press_outlets.json 허용 목록 밖 언론사의 기존 기사를 정리한다."""
    return {"deleted_count": purge_disallowed_articles()}


@router.get("/status")
def get_status():
    return {"last_sync_at": storage.get_meta("last_sync_at")}
