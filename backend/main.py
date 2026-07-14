from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_ROOT
from backend.routes import articles, auth, keywords, stocks, sync
from backend.services import storage

app = FastAPI(title="네이버 뉴스 키워드 대시보드")


@app.on_event("startup")
def on_startup():
    storage.init_db()


app.include_router(auth.router)
app.include_router(keywords.router)
app.include_router(stocks.router)
app.include_router(sync.router)
app.include_router(articles.router)

app.mount(
    "/", StaticFiles(directory=PROJECT_ROOT / "frontend", html=True), name="frontend"
)
