from fastapi import APIRouter, Depends, HTTPException

from backend.models.schemas import Keyword, KeywordCreate, StockSnapshot
from backend.services import pipeline_state, storage
from backend.services.auth import require_auth
from backend.services.stock_lookup import chart_image_url, get_stock_snapshot, resolve_stock_code
from backend.services.validators import validate_keyword_input

router = APIRouter(
    prefix="/api/keywords", tags=["keywords"], dependencies=[Depends(require_auth)]
)


@router.get("", response_model=list[Keyword])
def get_keywords():
    return storage.list_keywords()


@router.post("", response_model=Keyword, status_code=201)
def create_keyword(payload: KeywordCreate):
    existing = [k["keyword"] for k in storage.list_keywords()]
    ok, error = validate_keyword_input(payload.keyword, existing)
    pipeline_state.record_step(
        "keyword-validated", "pass" if ok else "fail", data=payload.keyword
    )
    if not ok:
        raise HTTPException(status_code=400, detail=error)

    keyword = payload.keyword.strip()
    # 종목명이면 네이버 증권 종목코드를 함께 저장해 차트를 보여줄 수 있게 한다.
    # 조회 실패해도(네트워크 오류, 일반 키워드 등) 뉴스 키워드 등록 자체는 계속 진행한다.
    stock = resolve_stock_code(keyword)
    storage.add_keyword(
        keyword,
        stock_code=stock["code"] if stock else None,
        stock_name=stock["name"] if stock else None,
    )
    created = next(k for k in storage.list_keywords() if k["keyword"] == keyword)
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

    return {**snapshot, "chart_url": chart_image_url(keyword["stock_code"])}
