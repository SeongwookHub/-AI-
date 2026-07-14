from pydantic import BaseModel


class KeywordCreate(BaseModel):
    keyword: str


class LoginRequest(BaseModel):
    password: str


class Keyword(BaseModel):
    id: int
    keyword: str
    created_at: str
    stock_code: str | None = None
    stock_name: str | None = None


class StockSnapshot(BaseModel):
    price: str | None
    change: str | None
    change_ratio: str | None
    direction: str | None
    market_status: str | None
    market_status_label: str
    open_price: str | None
    high_price: str | None
    low_price: str | None
    volume: str | None
    nxt_price: str | None
    nxt_change: str | None
    nxt_change_ratio: str | None
    nxt_direction: str | None
    chart_url: str
    item_page_url: str


class ResearchReport(BaseModel):
    title: str
    broker: str
    date: str
    pdf_url: str | None
    detail_url: str


class Article(BaseModel):
    id: int
    link: str
    title: str
    description: str
    pub_date: str
    synced_at: str
    keywords: list[str]


class SyncResult(BaseModel):
    synced_at: str
    per_keyword_new_count: dict[str, int]
    failed_keywords: list[str]
    excluded_by_outlet: int
