REQUIRED_ARTICLE_FIELDS = ("title", "link", "pub_date")


def validate_keyword_input(keyword: str, existing_keywords: list[str]) -> tuple[bool, str]:
    """빈 값/중복 여부를 검사한다. (통과 여부, 에러 메시지)"""
    keyword = keyword.strip()
    if not keyword:
        return False, "키워드는 빈 값일 수 없습니다."
    if keyword in existing_keywords:
        return False, f"'{keyword}'는 이미 등록된 키워드입니다."
    return True, ""


def validate_article_schema(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """필수 필드(title, link, pub_date)가 모두 존재하는 항목만 통과시킨다.

    Returns: (valid_items, invalid_items)
    """
    valid, invalid = [], []
    for item in items:
        if all(item.get(field) for field in REQUIRED_ARTICLE_FIELDS):
            valid.append(item)
        else:
            invalid.append(item)
    return valid, invalid


def dedup_by_link(items: list[dict]) -> list[dict]:
    """동일 배치 내에서 link가 중복되는 항목을 제거하고 유일성을 확보한다."""
    seen: set[str] = set()
    result = []
    for item in items:
        link = item.get("link")
        if link and link not in seen:
            seen.add(link)
            result.append(item)
    return result
