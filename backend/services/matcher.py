def match_keywords(article: dict, keywords: list[str]) -> list[str]:
    """기사의 제목/설명에 문자열이 포함되는 키워드만 반환한다 (단순 포함 매칭, 대소문자 무시)."""
    haystack = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return [kw for kw in keywords if kw.lower() in haystack]
