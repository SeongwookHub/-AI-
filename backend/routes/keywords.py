from fastapi import APIRouter, Depends, HTTPException

from backend.models.schemas import Keyword, KeywordCreate
from backend.services import pipeline_state, storage
from backend.services.auth import require_auth
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

    storage.add_keyword(payload.keyword.strip())
    created = next(
        k for k in storage.list_keywords() if k["keyword"] == payload.keyword.strip()
    )
    return created


@router.delete("/{keyword_id}", status_code=204)
def remove_keyword(keyword_id: int):
    storage.delete_keyword(keyword_id)
