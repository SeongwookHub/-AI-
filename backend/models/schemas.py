from pydantic import BaseModel


class KeywordCreate(BaseModel):
    keyword: str


class LoginRequest(BaseModel):
    password: str


class Keyword(BaseModel):
    id: int
    keyword: str
    created_at: str


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
