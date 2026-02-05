import datetime


def test_get_topics(
        test_client,
):
    response = test_client.get("/topics/")
    assert response.status_code == 200
    assert len(response.json()) == 4
    # for topic in response.json():
    #     db_topic = list(filter(lambda a: a.id == topic["id"], sample_db_topics))[0]
    #     assert topic["name"] == db_topic.name


def test_get_topic(
        test_client
):
    """
    get the details of a single topic but also doubles as a filter for articles by topic
    """
    test_id = 1
    response = test_client.get(f"/topic/{test_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == test_id


def test_get_topic_not_found(test_client):
    """Test that requesting a non-existent topic returns 404"""
    response = test_client.get("/topic/99999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Topic not found"


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


def test_get_articles_with_topic_filter(test_client, fake_articles):
    """Test filtering articles by topic_id"""
    # Get articles for topic_id=1 (Technology)
    response = test_client.get("/articles/?topic_id=1")
    assert response.status_code == 200
    articles = response.json()

    # Should only return articles with technology topic
    assert len(articles) > 0
    for article in articles:
        topic_ids = [t["id"] for t in article["topics"]]
        assert 1 in topic_ids


def test_get_articles_with_pagination_limit(test_client, fake_articles):
    # Test with limit parameter only
    response = test_client.get("/articles/?limit=1")
    assert response.status_code == 200
    limited = response.json()
    assert len(limited) == 1


def test_get_articles_with_pagination_skip(test_client, fake_articles):
    total_articles = len(fake_articles)

    response = test_client.get(f"/articles/?skip=1")
    assert response.status_code == 200
    assert len(response.json()) == total_articles - 1


# Tests for /daily-summaries/ endpoint


def test_get_daily_summaries_default_today(test_client_with_summaries):
    """Test getting daily summaries defaults to today and returns all summaries up to today"""
    response = test_client_with_summaries.get("/daily-summaries/")
    assert response.status_code == 200
    summaries = response.json()

    # Should return all summaries up to today (4 total: 2 from today + 2 from yesterday)
    assert len(summaries) == 4

    today = datetime.date.today()
    for summary in summaries:
        # All summaries should be on or before today
        assert summary["date"] <= str(today)
        assert summary["summary"] is not None
        assert "topic" in summary
        assert "articles" in summary
        assert len(summary["articles"]) > 0


def test_get_daily_summaries_specific_date(test_client_with_summaries):
    """Test filtering daily summaries up to a specific date"""
    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    response = test_client_with_summaries.get(f"/daily-summaries/?date={yesterday}")
    assert response.status_code == 200
    summaries = response.json()

    # Should return summaries up to yesterday (2 summaries: tech and business from yesterday)
    assert len(summaries) == 2

    for summary in summaries:
        # All summaries should be on or before yesterday
        assert summary["date"] <= str(yesterday)
        assert summary["summary"] is not None


def test_get_daily_summaries_filter_by_topic(test_client_with_summaries):
    """Test filtering daily summaries by topic_id"""
    today = datetime.date.today()

    # Filter for technology topic (topic_id=1)
    response = test_client_with_summaries.get(f"/daily-summaries/?date={today}&topic_id=1")
    assert response.status_code == 200
    summaries = response.json()

    # Should return technology summaries up to today (2: today and yesterday)
    assert len(summaries) == 2
    for summary in summaries:
        assert summary["topic"]["id"] == 1
        assert summary["topic"]["name"] == "TECHNOLOGY"


def test_get_daily_summaries_no_results(test_client_with_summaries):
    """Test daily summaries returns empty list when no data before date"""
    # Use a date before all test data (oldest is yesterday)
    old_date = datetime.date.today() - datetime.timedelta(days=30)

    response = test_client_with_summaries.get(f"/daily-summaries/?date={old_date}")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_daily_summaries_includes_articles(test_client_with_summaries):
    """Test that daily summaries include their linked articles"""
    today = datetime.date.today()

    response = test_client_with_summaries.get(f"/daily-summaries/?date={today}")
    assert response.status_code == 200
    summaries = response.json()

    # Find today's technology summary (should be first due to desc ordering)
    tech_summaries = [s for s in summaries if s["topic"]["name"] == "TECHNOLOGY"]
    # There are 2 tech summaries (today and yesterday)
    assert len(tech_summaries) == 2

    # Today's tech summary should have 2 articles
    today_tech_summary = next(s for s in tech_summaries if s["date"] == str(today))
    assert len(today_tech_summary["articles"]) == 2

    # Verify article structure
    for article in today_tech_summary["articles"]:
        assert "id" in article
        assert "title" in article
        assert "url" in article
        assert "topics" in article


def test_get_daily_summaries_pagination(test_client_with_summaries):
    """Test pagination on daily summaries endpoint"""
    today = datetime.date.today()

    # Test with limit parameter
    response = test_client_with_summaries.get(f"/daily-summaries/?limit=1")
    assert response.status_code == 200
    limited = response.json()
    assert len(limited) == 1


def test_get_daily_summaries_topic_structure(test_client_with_summaries):
    """Test that topic information is properly included"""
    response = test_client_with_summaries.get("/daily-summaries/")
    assert response.status_code == 200
    summaries = response.json()

    assert len(summaries) > 0
    for summary in summaries:
        topic = summary["topic"]
        assert "id" in topic
        assert "name" in topic
        assert isinstance(topic["id"], int)
        assert isinstance(topic["name"], str)
