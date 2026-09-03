import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { DayHeader } from './components/DayHeader';
import { TopicBar } from './components/TopicBar';
import { ArticleList } from './components/ArticleList';
import { SearchResults } from './components/SearchResults';
import { useKeywords } from './hooks/useKeywords';
import { useKeywordUpdates } from './hooks/useKeywordUpdates';
import { useSearch } from './hooks/useSearch';
import type { Article, ArticleSearchResult, Keyword } from './data-model/keyword';
import { dayTitle, daySubtitle, shiftDate, utcISODate } from './lib/dates';
import './App.css';

/** Keywords with fewer articles than this are hidden from the topic bar. */
const MIN_ARTICLES = 2;
/** How many articles each topic shows in the "All" overview. */
const PREVIEW_PER_TOPIC = 4;

function App() {
  // Recomputed on an interval so a tab left open past UTC midnight rolls over.
  const [today, setToday] = useState(() => utcISODate(new Date()));
  useEffect(() => {
    const id = setInterval(() => setToday(utcISODate(new Date())), 60_000);
    return () => clearInterval(id);
  }, []);

  const [selectedDate, setSelectedDate] = useState(today);
  const isToday = selectedDate === today;

  // null = the "All" overview
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);

  const [inputValue, setInputValue] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { data: fetchedKeywords, isLoading, isError } = useKeywords(selectedDate);

  // Live updates only ever write today's entry; any other date reads straight from the fetch.
  // Navigating to a past date therefore can never be overwritten by a WebSocket push.
  const [liveCache, setLiveCache] = useState<Map<string, Keyword[]>>(new Map());
  const handleWsUpdate = useCallback(
    (keywords: Keyword[]) => setLiveCache((prev) => new Map(prev).set(today, keywords)),
    [today],
  );
  useKeywordUpdates(handleWsUpdate);

  const keywords = liveCache.get(selectedDate) ?? fetchedKeywords;

  const { data: searchResults = [] as ArticleSearchResult[], isFetching: isSearching } = useSearch(submittedQuery);
  const isSearchMode = submittedQuery.trim().length > 0;

  const visibleKeywords = useMemo(
    () => (keywords ?? []).filter((kw) => kw.articles.length >= MIN_ARTICLES),
    [keywords],
  );

  const sources = useMemo(() => {
    const seen = new Map<string, { name: string; icon_url: string | null }>();
    for (const kw of keywords ?? []) {
      for (const a of kw.articles) {
        if (a.source_name && !seen.has(a.source_name)) {
          seen.set(a.source_name, { name: a.source_name, icon_url: a.source_icon_url });
        }
      }
    }
    return [...seen.values()];
  }, [keywords]);

  const totalArticles = useMemo(() => {
    const ids = new Set<number>();
    for (const kw of keywords ?? []) for (const a of kw.articles) ids.add(a.id);
    return ids.size;
  }, [keywords]);

  const matchesSource = (a: Article) => selectedSource === null || a.source_name === selectedSource;

  const tabs = visibleKeywords.map((kw) => ({
    text: kw.text,
    count: kw.articles.filter(matchesSource).length,
  }));
  const allCount = tabs.reduce((n, t) => n + t.count, 0);

  // Looked up in the full list so single-article keywords (hidden from the bar) still open when clicked.
  const selectedKeyword = selectedTopic === null ? null : (keywords?.find((kw) => kw.text === selectedTopic) ?? null);

  function selectDate(next: string) {
    setSelectedDate(next);
    setSelectedTopic(null);
    setSelectedSource(null);
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmittedQuery(inputValue.trim());
    window.scrollTo({ top: 0 });
  }

  function clearSearch() {
    setInputValue('');
    setSubmittedQuery('');
    searchInputRef.current?.focus();
  }

  function selectTopic(text: string | null) {
    setSelectedTopic(text);
    setSubmittedQuery('');
    setInputValue('');
    window.scrollTo({ top: 0 });
  }

  const dateTitle = dayTitle(selectedDate, today);
  const dateSubtitle = keywords
    ? [
        daySubtitle(selectedDate, today),
        `${totalArticles} ${totalArticles === 1 ? 'article' : 'articles'}`,
        ...(sources.length > 0 ? [`${sources.length} ${sources.length === 1 ? 'source' : 'sources'}`] : []),
      ].join(' · ')
    : daySubtitle(selectedDate, today);

  function renderArticles() {
    if (isLoading || !keywords) {
      return (
        <div className="loading-container loading-container--inline">
          <div className="loading-spinner" />
        </div>
      );
    }

    if (visibleKeywords.length === 0) {
      return <p className="empty-state">No articles for this day yet.</p>;
    }

    if (selectedKeyword) {
      const articles = selectedKeyword.articles.filter(matchesSource);
      return articles.length > 0 ? (
        <ArticleList articles={articles} hideKeyword={selectedKeyword.text} onKeywordClick={selectTopic} />
      ) : (
        <p className="empty-state">
          Nothing from {selectedSource} in <span className="empty-state__topic">{selectedKeyword.text}</span>.
        </p>
      );
    }

    const sections = visibleKeywords
      .map((kw) => ({ kw, articles: kw.articles.filter(matchesSource) }))
      .filter((s) => s.articles.length > 0);

    if (sections.length === 0) {
      return <p className="empty-state">Nothing from {selectedSource} on this day.</p>;
    }

    return sections.map(({ kw, articles }) => (
      <section className="topic-section" key={kw.text}>
        <div className="topic-section__head">
          <h2 className="topic-section__title">{kw.text}</h2>
          <span className="topic-section__count">{articles.length}</span>
          {articles.length > PREVIEW_PER_TOPIC && (
            <button className="topic-section__more" onClick={() => selectTopic(kw.text)}>
              View all
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="m9 6 6 6-6 6" />
              </svg>
            </button>
          )}
        </div>
        <ArticleList
          articles={articles.slice(0, PREVIEW_PER_TOPIC)}
          hideKeyword={kw.text}
          onKeywordClick={selectTopic}
        />
      </section>
    ));
  }

  return (
    <div className="app">
      <header className="header">
        <a className="header__brand" href="/" onClick={(e) => { e.preventDefault(); clearSearch(); selectDate(today); window.scrollTo({ top: 0 }); }}>
          <span className="header__logo" aria-hidden="true">↗</span>
          <span className="header__title">Trend Engine</span>
        </a>

        <form className="header__search" onSubmit={handleSearchSubmit} role="search">
          <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <line x1="16.5" y1="16.5" x2="21" y2="21" />
          </svg>
          <input
            ref={searchInputRef}
            className="search-input"
            type="search"
            placeholder="Search articles…"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          {isSearchMode && (
            <button type="button" className="search-clear" onClick={clearSearch} aria-label="Clear search">
              ✕
            </button>
          )}
        </form>
      </header>

      <main className="page">
        {isError ? (
          <div className="empty-state empty-state--error">
            <h2>Couldn’t load articles</h2>
            <p>Check that the API is running, then reload.</p>
          </div>
        ) : isSearchMode ? (
          <SearchResults
            key={submittedQuery}
            query={submittedQuery}
            results={searchResults}
            isLoading={isSearching}
            onClear={clearSearch}
            onKeywordClick={selectTopic}
          />
        ) : (
          <>
            <DayHeader
              title={dateTitle}
              subtitle={dateSubtitle}
              isLive={isToday}
              hasNewer={!isToday}
              onNewer={() => selectDate(shiftDate(selectedDate, 1))}
              onOlder={() => selectDate(shiftDate(selectedDate, -1))}
            />
            {keywords && visibleKeywords.length > 0 && (
              <TopicBar
                tabs={tabs}
                allCount={allCount}
                selected={selectedKeyword ? selectedKeyword.text : null}
                onSelect={selectTopic}
                sources={sources}
                selectedSource={selectedSource}
                onSelectSource={setSelectedSource}
              />
            )}
            {renderArticles()}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
