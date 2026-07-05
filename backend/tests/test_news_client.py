from app.services import news_client

RSS_SAMPLE = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<item><title>RSS headline one</title><pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate></item>
<item><title>RSS headline two</title><pubDate>Mon, 01 Jan 2026 01:00:00 GMT</pubDate></item>
</channel></rss>
"""

ATOM_SAMPLE = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>8-K - ACME CORP (0000123456) (Filer)</title><updated>2026-01-01T00:00:00-05:00</updated></entry>
<entry><title>8-K - WIDGET INC (0000654321) (Filer)</title><updated>2026-01-01T01:00:00-05:00</updated></entry>
</feed>
"""


def test_parse_feed_handles_rss_items():
    result = news_client._parse_feed("Test RSS", RSS_SAMPLE, limit=10)
    assert len(result) == 2
    assert result[0] == {
        "title": "RSS headline one",
        "published_at": "Mon, 01 Jan 2026 00:00:00 GMT",
        "source": "Test RSS",
    }


def test_parse_feed_handles_atom_entries():
    result = news_client._parse_feed("SEC EDGAR", ATOM_SAMPLE, limit=10)
    assert len(result) == 2
    assert result[0]["title"] == "8-K - ACME CORP (0000123456) (Filer)"
    assert result[0]["published_at"] == "2026-01-01T00:00:00-05:00"
    assert result[0]["source"] == "SEC EDGAR"


def test_parse_feed_respects_limit():
    result = news_client._parse_feed("Test RSS", RSS_SAMPLE, limit=1)
    assert len(result) == 1


def test_interleave_round_robins_across_sources_instead_of_concatenating():
    groups = [
        [{"title": "a1"}, {"title": "a2"}],
        [{"title": "b1"}],
        [{"title": "c1"}, {"title": "c2"}, {"title": "c3"}],
    ]
    result = news_client._interleave(groups)
    assert [item["title"] for item in result] == ["a1", "b1", "c1", "a2", "c2", "c3"]


def test_get_headlines_truncates_after_interleaving(monkeypatch):
    def fake_rss(source, url, limit, params=None):
        return [{"title": f"{source}-{i}", "published_at": "", "source": source} for i in range(3)]

    def fake_reddit(subreddit, limit):
        return [{"title": f"reddit-{subreddit}", "published_at": "", "source": f"Reddit r/{subreddit}"}]

    monkeypatch.setattr(news_client, "_get_rss", fake_rss)
    monkeypatch.setattr(news_client, "_get_reddit", fake_reddit)

    client = news_client.NewsClient(settings=None)
    result = client.get_headlines(["SPY"], limit=5)

    assert len(result) == 5


def test_get_headlines_degrades_gracefully_when_a_source_raises(monkeypatch):
    def flaky_rss(source, url, limit, params=None):
        if source == news_client.RSS_FEEDS[0][0]:
            raise RuntimeError("network hiccup")
        return [{"title": f"{source}-headline", "published_at": "", "source": source}]

    def fake_reddit(subreddit, limit):
        return []

    monkeypatch.setattr(news_client, "_get_rss", flaky_rss)
    monkeypatch.setattr(news_client, "_get_reddit", fake_reddit)

    client = news_client.NewsClient(settings=None)
    result = client.get_headlines([], limit=100)

    # One source blew up; the rest still contributed headlines.
    assert len(result) == len(news_client.RSS_FEEDS) - 1


def test_get_new_ticker_headlines_detects_a_fresh_headline(monkeypatch):
    def fake_ticker_headlines(ticker, limit):
        return [
            {"title": "Old headline", "published_at": "", "source": f"Yahoo Finance ({ticker})"},
            {"title": "BREAKING: earnings beat", "published_at": "", "source": f"Yahoo Finance ({ticker})"},
        ]

    monkeypatch.setattr(news_client, "_get_ticker_headlines", fake_ticker_headlines)

    client = news_client.NewsClient(settings=None)
    seen = {"SPY": ["Old headline"]}

    new_headlines, updated_seen = client.get_new_ticker_headlines(["SPY"], seen)

    assert len(new_headlines) == 1
    assert new_headlines[0]["title"] == "BREAKING: earnings beat"
    assert updated_seen["SPY"] == ["Old headline", "BREAKING: earnings beat"]


def test_get_new_ticker_headlines_nothing_new_when_unchanged(monkeypatch):
    def fake_ticker_headlines(ticker, limit):
        return [{"title": "Same headline", "published_at": "", "source": f"Yahoo Finance ({ticker})"}]

    monkeypatch.setattr(news_client, "_get_ticker_headlines", fake_ticker_headlines)

    client = news_client.NewsClient(settings=None)
    seen = {"SPY": ["Same headline"]}

    new_headlines, _ = client.get_new_ticker_headlines(["SPY"], seen)

    assert new_headlines == []


def test_get_new_ticker_headlines_keeps_prior_seen_state_when_fetch_fails(monkeypatch):
    def failing_ticker_headlines(ticker, limit):
        raise RuntimeError("network hiccup")

    monkeypatch.setattr(news_client, "_get_ticker_headlines", failing_ticker_headlines)

    client = news_client.NewsClient(settings=None)
    seen = {"SPY": ["Existing headline"]}

    new_headlines, updated_seen = client.get_new_ticker_headlines(["SPY"], seen)

    assert new_headlines == []
    assert updated_seen["SPY"] == ["Existing headline"]
