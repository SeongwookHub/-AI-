from fastapi import APIRouter, Depends, HTTPException

from backend.services import storage
from backend.services.auth import require_auth

router = APIRouter(
    prefix="/api/articles", tags=["articles"], dependencies=[Depends(require_auth)]
)


@router.get("")
def get_articles(keyword_id: int | None = None):
    if keyword_id is None:
        return storage.list_unclassified_articles()

    if not any(k["id"] == keyword_id for k in storage.list_keywords()):
        raise HTTPException(status_code=404, detail="존재하지 않는 키워드입니다.")

    return storage.list_articles_for_keyword(keyword_id)
