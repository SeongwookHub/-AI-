import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_ROOT
from backend.routes import articles, auth, keywords, stocks, sync
from backend.services import storage
from backend.services.stock_universe import get_stock_universe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """예상하지 못한 예외는 전체 스택트레이스를 서버 로그에만 남기고,
    사용자에게는 깔끔한 500 메시지만 내려준다 (의도적으로 던지는 HTTPException은
    이 핸들러를 거치지 않고 원래대로 동작한다)."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "서버에서 예상하지 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요."},
    )


app.include_router(auth.router)
app.include_router(keywords.router)
app.include_router(stocks.router)
app.include_router(sync.router)
app.include_router(articles.router)

app.mount(
    "/", StaticFiles(directory=PROJECT_ROOT / "frontend", html=True), name="frontend"
)
