import re

from fastapi import APIRouter, Depends, HTTPException

from backend.models.schemas import Keyword, KeywordCreate, StockSnapshot
from backend.services import pipeline_state, storage
from backend.services.auth import require_auth
from backend.services.stock_lookup import chart_image_url, get_stock_snapshot, item_page_url
from backend.services.stock_universe import find_stock_by_code, find_stock_by_name
from backend.services.validators import validate_keyword_input

router = APIRouter(
    prefix="/api/keywords", tags=["keywords"], dependencies=[Depends(require_auth)]
)

_CODE_RE = re.compile(r"\d{6}")


@router.get("", response_model=list[Keyword])
def get_keywords():
    return storage.list_keywords()


@router.post("", response_model=Keyword, status_code=201)
def create_keyword(payload: KeywordCreate):
    query = payload.keyword.strip()

    stock = find_stock_by_code(query) if _CODE_RE.fullmatch(query) else find_stock_by_name(query)
    if not stock:
        raise HTTPException(
            status_code=400,
            detail="코스피/코스닥에 상장된 종목명 또는 종목코드만 등록할 수 있습니다.",
        )

    existing = [k["keyword"] for k in storage.list_keywords()]
    ok, error = validate_keyword_input(stock["name"], existing)
    pipeline_state.record_step("keyword-validated", "pass" if ok else "fail", data=stock["name"])
    if not ok:
        raise HTTPException(status_code=400, detail=error)

    storage.add_keyword(stock["name"], stock_code=stock["code"], stock_name=stock["name"])
    created = next(k for k in storage.list_keywords() if k["keyword"] == stock["name"])
    return created


@router.delete("/{keyword_id}", status_code=204)
def remove_keyword(keyword_id: int):
    storage.delete_keyword(keyword_id)


@router.get("/{keyword_id}/stock", response_model=StockSnapshot)
def get_stock(keyword_id: int):
    keyword = storage.get_keyword(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="존재하지 않는 키워드입니다.")
    if not keyword["stock_code"]:
        raise HTTPException(status_code=404, detail="종목으로 연결되지 않은 키워드입니다.")

    snapshot = get_stock_snapshot(keyword["stock_code"])
    if not snapshot:
        raise HTTPException(status_code=502, detail="네이버 증권 시세 조회에 실패했습니다.")

    return {
        **snapshot,
        "chart_url": chart_image_url(keyword["stock_code"]),
        "item_page_url": item_page_url(keyword["stock_code"]),
    }
