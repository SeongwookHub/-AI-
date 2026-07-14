import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_ROOT
from backend.routes import articles, auth, keywords, stocks, sync
from backend.services import storage
from backend.services.stock_universe import get_stock_universe

logger = logging.getLogger(__name__)

app = FastAPI(title="네이버 뉴스 키워드 대시보드")


@app.on_event("startup")
def on_startup():
    storage.init_db()
    # 첫 검색 요청 때 ~10초씩 걸리지 않도록, 서버 기동 시점에 종목 목록 캐시를 미리 데워둔다.
    # (배포 환경처럼 재시작이 잦은 곳에서는 매번 다시 데워야 하므로 실패해도 기동 자체는 막지 않는다.)
    try:
        get_stock_universe()
    except Exception:
        logger.exception("종목 목록 캐시 예열 실패 - 첫 검색 시 다시 시도됩니다.")


app.include_router(auth.router)
app.include_router(keywords.router)
app.include_router(stocks.router)
app.include_router(sync.router)
app.include_router(articles.router)

app.mount(
    "/", StaticFiles(directory=PROJECT_ROOT / "frontend", html=True), name="frontend"
)
