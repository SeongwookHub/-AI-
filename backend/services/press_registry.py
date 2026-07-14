import json
from urllib.parse import urlparse

from backend.config import PROJECT_ROOT

REGISTRY_PATH = PROJECT_ROOT / "backend" / "press_outlets.json"


def load_sector_outlets() -> dict:
    """섹터별 허용 언론사 목록을 로드한다. backend/press_outlets.json을 직접 편집해 조정할 수 있다."""
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def get_allowed_domains() -> set[str]:
    domains = set()
    for outlets in load_sector_outlets().values():
        for outlet in outlets:
            domains.add(outlet["domain"])
    return domains


def is_allowed_link(link: str, allowed_domains: set[str]) -> bool:
    hostname = urlparse(link).hostname
    if not hostname:
        return False
    hostname = hostname.lower()
    return any(hostname == d or hostname.endswith(f".{d}") for d in allowed_domains)


def filter_allowed_articles(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """허용된 언론사 도메인(backend/press_outlets.json)의 기사만 통과시킨다.

    Returns: (allowed_items, excluded_items)
    """
    allowed_domains = get_allowed_domains()
    allowed, excluded = [], []
    for item in items:
        if is_allowed_link(item.get("link", ""), allowed_domains):
            allowed.append(item)
        else:
            excluded.append(item)
    return allowed, excluded
