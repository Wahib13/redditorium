from unittest.mock import MagicMock

from pipeline.embeddings import embed_articles_batch


def test_embed_articles_batch_sets_embeddings(db_session, fake_articles):
    client = MagicMock()
    client.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]

    count = embed_articles_batch(fake_articles, client)

    assert count == 2
    client.embed_batch.assert_called_once()  # one batched call, not per-article
    assert fake_articles[0].embedding == [0.1] * 384
    assert fake_articles[1].embedding == [0.2] * 384


def test_embed_articles_batch_builds_title_plus_lede(db_session, fake_articles):
    client = MagicMock()
    client.embed_batch.return_value = [[0.0] * 384] * len(fake_articles)

    embed_articles_batch(fake_articles, client)

    texts = client.embed_batch.call_args.args[0]
    assert texts[0] == "AI Lives Rent Free In My Head a short lede summarising the story"


def test_embed_articles_batch_skips_empty(db_session, fake_articles):
    for a in fake_articles:
        a.title = None
        a.summary = None
    client = MagicMock()

    count = embed_articles_batch(fake_articles, client)

    assert count == 0
    client.embed_batch.assert_not_called()


def test_embed_articles_batch_respects_batch_size(db_session, fake_articles):
    client = MagicMock()
    client.embed_batch.side_effect = lambda texts: [[0.0] * 384 for _ in texts]

    count = embed_articles_batch(fake_articles, client, batch_size=1)

    assert count == 2
    assert client.embed_batch.call_count == 2  # one call per article at batch_size=1
