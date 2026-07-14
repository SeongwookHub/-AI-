from fastapi import APIRouter, Depends

from backend.services.auth import require_auth
from backend.services.stock_universe import search_stocks

router = APIRouter(prefix="/api/stocks", tags=["stocks"], dependencies=[Depends(require_auth)])


@router.get("/search")
def search(q: str = ""):
    """코스피/코스닥 상장 종목명(부분일치, 시작하는 것 우선) 또는 6자리 종목코드로 검색."""
    return search_stocks(q)
