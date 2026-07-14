def test_add_and_list_keywords(temp_storage):
    assert temp_storage.add_keyword("반도체") is True
    assert temp_storage.add_keyword("반도체") is False  # 중복
    keywords = temp_storage.list_keywords()
    assert [k["keyword"] for k in keywords] == ["반도체"]


def test_delete_keyword(temp_storage):
    temp_storage.add_keyword("반도체")
    kw_id = temp_storage.list_keywords()[0]["id"]
    temp_storage.delete_keyword(kw_id)
    assert temp_storage.list_keywords() == []


def test_upsert_article_new_then_duplicate_link(temp_storage):
    temp_storage.add_keyword("반도체")
    kw_id = temp_storage.list_keywords()[0]["id"]
    article = {
        "link": "http://example.com/1",
        "title": "삼성 반도체 실적",
        "description": "설명",
        "pub_date": "2026-07-14T09:00:00",
    }

    is_new_first = temp_storage.upsert_article(article, [kw_id])
    is_new_second = temp_storage.upsert_article(article, [kw_id])

    assert is_new_first is True
    assert is_new_second is False  # 동일 link는 upsert만, 신규 아님

    articles = temp_storage.list_articles_for_keyword(kw_id)
    assert len(articles) == 1  # 중복 저장되지 않음
    assert articles[0]["keywords"] == ["반도체"]


def test_upsert_article_merges_keywords_on_second_match(temp_storage):
    temp_storage.add_keyword("반도체")
    temp_storage.add_keyword("삼성전자")
    kw_rows = {k["keyword"]: k["id"] for k in temp_storage.list_keywords()}

    article = {
        "link": "http://example.com/2",
        "title": "삼성전자 반도체",
        "description": "",
        "pub_date": "2026-07-14T09:00:00",
    }
    temp_storage.upsert_article(article, [kw_rows["반도체"]])
    temp_storage.upsert_article(article, [kw_rows["반도체"], kw_rows["삼성전자"]])

    tagged = temp_storage.list_articles_for_keyword(kw_rows["삼성전자"])
    assert len(tagged) == 1
    assert set(tagged[0]["keywords"]) == {"반도체", "삼성전자"}


def test_unclassified_articles_have_no_keyword_tags(temp_storage):
    article = {
        "link": "http://example.com/3",
        "title": "미분류 기사",
        "description": "",
        "pub_date": "2026-07-14T09:00:00",
    }
    temp_storage.upsert_article(article, [])
    unclassified = temp_storage.list_unclassified_articles()
    assert len(unclassified) == 1
    assert unclassified[0]["keywords"] == []


def test_meta_set_and_get(temp_storage):
    assert temp_storage.get_meta("last_sync_at") is None
    temp_storage.set_meta("last_sync_at", "2026-07-14T10:00:00")
    assert temp_storage.get_meta("last_sync_at") == "2026-07-14T10:00:00"


def test_list_all_articles_and_delete(temp_storage):
    temp_storage.upsert_article(
        {"link": "http://a", "title": "A", "description": "", "pub_date": "2026-07-14"},
        [],
    )
    temp_storage.upsert_article(
        {"link": "http://b", "title": "B", "description": "", "pub_date": "2026-07-14"},
        [],
    )
    all_articles = temp_storage.list_all_articles()
    assert {a["link"] for a in all_articles} == {"http://a", "http://b"}

    deleted = temp_storage.delete_articles([all_articles[0]["id"]])
    assert deleted == 1
    assert len(temp_storage.list_all_articles()) == 1
