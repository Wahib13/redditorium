import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { DayCycler } from './components/DayCycler';
import { ArticleCard } from './components/ArticleCard';
import { SearchResults } from './components/SearchResults';
import { useKeywords } from './hooks/useKeywords';
import { useKeywordUpdates } from './hooks/useKeywordUpdates';
import { useSearch } from './hooks/useSearch';
import type { Keyword } from './data-model/keyword';
import './App.css';

// The server buckets articles by the UTC calendar day (see api.keywords.utc_today),
// so the frontend must reason about "today" and date navigation in UTC too.
function utcISODate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function shiftDate(dateStr: string, deltaDays: number): string {
  const d = new Date(dateStr + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + deltaDays);
  return utcISODate(d);
}

function formatDateLabel(dateStr: string, todayStr: string): string {
  if (dateStr === todayStr) return 'Today';
  const d = new Date(dateStr + 'T00:00:00Z');
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'UTC' });
}

function App() {
  // Recomputed on an interval so a tab left open past UTC midnight rolls over.
  const [today, setToday] = useState(() => utcISODate(new Date()));
  useEffect(() => {
    const id = setInterval(() => setToday(utcISODate(new Date())), 60_000);
    return () => clearInterval(id);
  }, []);

  const [selectedDate, setSelectedDate] = useState(today);
  const isToday = selectedDate === today;

  const [selectedKeywordId, setSelectedKeywordId] = useState<number | null>(null);
  const [selectedSourceName, setSelectedSourceName] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Date-keyed cache: WS updates write to cache[today]; navigation reads cache[selectedDate].
  // This ensures live updates never interfere with viewing a different date.
  const [keywordsCache, setKeywordsCache] = useState<Map<string, Keyword[]>>(new Map());
  const seededDates = useRef<Set<string>>(new Set());
  const lastAutoSelectDate = useRef<string | null>(null);

  const [inputValue, setInputValue] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { data: fetchedKeywords, isLoading, isError } = useKeywords(selectedDate);

  // Reset source filter when navigating dates
  useEffect(() => {
    setSelectedSourceName(null);
  }, [selectedDate]);

  // Seed cache from React Query fetch (once per date — WS takes over afterwards)
  useEffect(() => {
    if (!fetchedKeywords || seededDates.current.has(selectedDate)) return;
    seededDates.current.add(selectedDate);
    setKeywordsCache((prev) => new Map(prev).set(selectedDate, fetchedKeywords));
  }, [fetchedKeywords, selectedDate]);

  // Auto-select first visible keyword whenever we first arrive at a date's data
  const liveKeywords = keywordsCache.get(selectedDate);
  useEffect(() => {
    if (!liveKeywords || lastAutoSelectDate.current === selectedDate) return;
    lastAutoSelectDate.current = selectedDate;
    const visible = liveKeywords.filter((k) => k.articles.length >= 2);
    if (visible.length > 0) {
      setSelectedKeywordId(visible[0].id);
    }
  }, [liveKeywords, selectedDate]);

  // WS updates today's cache entry only — never touches other dates
  const handleWsUpdate = useCallback((keywords: Keyword[]) => {
    setKeywordsCache((prev) => new Map(prev).set(today, keywords));
  }, [today]);

  useKeywordUpdates(handleWsUpdate);

  const { data: searchResults = [] as import('./data-model/keyword').ArticleSearchResult[], isFetching: isSearching } = useSearch(submittedQuery);

  const isSearchMode = submittedQuery.trim().length > 0;

  const visibleKeywords = liveKeywords?.filter((kw) => kw.articles.length >= 2);

  const availableSources = useMemo(() => {
    if (!liveKeywords) return [];
    const seen = new Map<string, { name: string; icon_url: string | null }>();
    for (const kw of liveKeywords) {
      for (const a of kw.articles) {
        if (a.source_name && !seen.has(a.source_name)) {
          seen.set(a.source_name, { name: a.source_name, icon_url: a.source_icon_url });
        }
      }
    }
    return [...seen.values()];
  }, [liveKeywords]);

  function goOlder() {
    setSelectedDate((d) => shiftDate(d, -1));
  }

  function goNewer() {
    setSelectedDate((d) => shiftDate(d, 1));
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmittedQuery(inputValue.trim());
  }

  function clearSearch() {
    setInputValue('');
    setSubmittedQuery('');
    searchInputRef.current?.focus();
  }

  // Look up from full list so single-article keywords (hidden from sidebar) still work when clicked
  const selectedKeyword =
    liveKeywords?.find((kw) => kw.id === selectedKeywordId) ?? visibleKeywords?.[0] ?? null;

  function handleKeywordClick(kwId: number) {
    setSelectedKeywordId(kwId);
    setSubmittedQuery('');
    setInputValue('');
    setIsSidebarOpen(false);
  }

  if (isError) {
    return (
      <div className="app">
        <div className="error-container">
          <h2>Failed to load keywords</h2>
          <p>Please try again later.</p>
        </div>
      </div>
    );
  }

  if (isLoading || !liveKeywords) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="navbar">
        {!isSearchMode && (
          <button
            className="navbar__hamburger"
            onClick={() => setIsSidebarOpen((o) => !o)}
            aria-label="Toggle menu"
          >
            <span className="navbar__hamburger-bar" />
            <span className="navbar__hamburger-bar" />
            <span className="navbar__hamburger-bar" />
          </button>
        )}
        <div className="navbar__brand">
          <span className="navbar__logo" aria-hidden="true">
            ↗
          </span>
          <span className="navbar__title">Trend Engine</span>
          {isToday && !isSearchMode && (
            <span className="live-badge">
              <span className="live-badge__dot" />
              live
            </span>
          )}
        </div>

        <form className="navbar__search" onSubmit={handleSearchSubmit}>
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

      {isSearchMode ? (
        <div className="app-body">
          <SearchResults
            key={submittedQuery}
            query={submittedQuery}
            results={searchResults}
            isLoading={isSearching}
            onClear={clearSearch}
            onKeywordClick={handleKeywordClick}
            selectedKeywordId={selectedKeywordId}
          />
        </div>
      ) : (
        <div className="app-body">
          {isSidebarOpen && (
            <div className="sidebar-overlay" onClick={() => setIsSidebarOpen(false)} />
          )}
          <aside className={`sidebar${isSidebarOpen ? ' sidebar--open' : ''}`}>
            <div className="sidebar__day-nav">
              <DayCycler
                label={formatDateLabel(selectedDate, today)}
                hasNewer={!isToday}
                hasOlder={true}
                onNewer={goNewer}
                onOlder={goOlder}
              />
            </div>

            <p className="sidebar__section-heading">Trending</p>
            <nav className="sidebar__keyword-list" aria-label="Keywords">
              {visibleKeywords?.map((kw) => (
                <button
                  key={kw.id ?? kw.text}
                  className={`keyword-item${selectedKeywordId === kw.id ? ' keyword-item--active' : ''}`}
                  onClick={() => { setSelectedKeywordId(kw.id); setIsSidebarOpen(false); }}
                >
                  <span className="keyword-item__text">{kw.text}</span>
                  <span className="keyword-item__count">{kw.articles.length}</span>
                </button>
              ))}
              {visibleKeywords?.length === 0 && (
                <p className="main-content__empty">No keywords for this day.</p>
              )}
            </nav>

            {availableSources.length > 0 && (
              <div className="sidebar__sources">
                <p className="sidebar__sources-heading">Sources</p>
                <button
                  className={`source-item${selectedSourceName === null ? ' source-item--active' : ''}`}
                  onClick={() => { setSelectedSourceName(null); setIsSidebarOpen(false); }}
                >
                  All
                </button>
                {availableSources.map((src) => (
                  <button
                    key={src.name}
                    className={`source-item${selectedSourceName === src.name ? ' source-item--active' : ''}`}
                    onClick={() => { setSelectedSourceName((prev) => prev === src.name ? null : src.name); setIsSidebarOpen(false); }}
                  >
                    {src.icon_url && <img className="source-item__icon" src={src.icon_url} alt="" />}
                    {src.name}
                  </button>
                ))}
              </div>
            )}
          </aside>

          <main className="main-content">
            {selectedKeyword ? (
              <div className="articles-list">
                {selectedKeyword.articles
                  .filter((a) => selectedSourceName === null || a.source_name === selectedSourceName)
                  .map((article) => (
                    <ArticleCard key={article.id} article={article} onKeywordClick={handleKeywordClick} selectedKeywordId={selectedKeywordId} />
                  ))}
              </div>
            ) : (
              <p className="main-content__empty">Select a keyword to see articles.</p>
            )}
          </main>

          {availableSources.length > 0 && (
            <aside className="source-panel">
              <p className="source-panel__heading">Sources</p>
              <button
                className={`source-item${selectedSourceName === null ? ' source-item--active' : ''}`}
                onClick={() => setSelectedSourceName(null)}
              >
                All
              </button>
              {availableSources.map((src) => (
                <button
                  key={src.name}
                  className={`source-item${selectedSourceName === src.name ? ' source-item--active' : ''}`}
                  onClick={() => setSelectedSourceName((prev) => prev === src.name ? null : src.name)}
                >
                  {src.icon_url && (
                    <img className="source-item__icon" src={src.icon_url} alt="" />
                  )}
                  {src.name}
                </button>
              ))}
            </aside>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
