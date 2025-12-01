from db.models import Story
from ingestion.hackernews import fetch_stories


def test_new_stories(
        mock_hackernews_api,
        db_session,
        sample_stories,
):
    mock_hackernews_api.fetch_stories.return_value = [story.id for story in sample_stories]

    def fetch_story_side_effect(story_id):
        return next(s for s in sample_stories if s.id == story_id)

    mock_hackernews_api.fetch_story.side_effect = fetch_story_side_effect

    fetch_stories(
        mock_hackernews_api,
        db_session,
    )

    db_results = db_session.query(Story).all()

    assert len(db_results) == len(sample_stories)
    for db_story in db_results:
        expected_story = next(filter(lambda story: story.id == db_story.hacker_news_id, sample_stories))
        assert db_story.title == expected_story.title
        assert db_story.url == str(expected_story.url)
        assert db_story.type == expected_story.type.value

# def test_duplicate_stories():
#     ...
#
#
# def test_idempotency_multiple_runs():
#     ...
