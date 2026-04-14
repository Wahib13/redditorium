def test_get_keywords(test_client):
    response = test_client.get("/keywords/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_keyword_not_found(test_client):
    response = test_client.get("/keyword/99999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Keyword not found"


def test_get_articles(
        test_client,
        fake_articles,
):
    response = test_client.get("/articles/")
    assert response.status_code == 200
    assert len(response.json()) == len(fake_articles)
    for article in response.json():
        db_article = list(filter(lambda a: a.id == article["id"], fake_articles))[0]
        assert article["title"] == db_article.title


def test_get_article(
        test_client,
):
    test_id = 1
    response = test_client.get(f"/article/{test_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == test_id


def test_get_article_not_found(test_client):
    """Test that requesting a non-existent article returns 404"""
    response = test_client.get("/article/99999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Article not found"


def test_get_articles_with_pagination_limit(test_client, fake_articles):
    response = test_client.get("/articles/?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_articles_with_pagination_skip(test_client, fake_articles):
    total_articles = len(fake_articles)
    response = test_client.get("/articles/?skip=1")
    assert response.status_code == 200
    assert len(response.json()) == total_articles - 1
