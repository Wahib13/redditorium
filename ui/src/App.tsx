import { useEffect, useRef, useState } from 'react';
import { DayCycler } from './components/DayCycler';
import { ArticleCard } from './components/ArticleCard';
import { SearchResults } from './components/SearchResults';
import { useKeywords } from './hooks/useKeywords';
import { useKeywordUpdates } from './hooks/useKeywordUpdates';
import { useSearch } from './hooks/useSearch';
import './App.css';

function toLocalISODate(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatDateLabel(dateStr: string, todayStr: string): string {
  if (dateStr === todayStr) return 'Today';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}

const today = toLocalISODate(new Date());

function App() {
  const [selectedDate, setSelectedDate] = useState(today);
  const isToday = selectedDate === today;

  const [selectedKeywordId, setSelectedKeywordId] = useState<number | null>(null);

  const [inputValue, setInputValue] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { data: keywords, isLoading, isError } = useKeywords(selectedDate);
  useKeywordUpdates(selectedDate);

  const { data: searchResults = [] as import('./data-model/keyword').ArticleSearchResult[], isFetching: isSearching } = useSearch(submittedQuery);

  const isSearchMode = submittedQuery.trim().length > 0;

  const visibleKeywords = keywords?.filter((kw) => kw.articles.length >= 2);

  // Keep selection in sync across date changes — no explicit reset needed
  useEffect(() => {
    if (visibleKeywords && visibleKeywords.length > 0) {
      setSelectedKeywordId((prev) => {
        if (prev !== null && visibleKeywords.some((k) => k.id === prev)) return prev;
        return visibleKeywords[0].id;
      });
    }
  }, [keywords]); // eslint-disable-line react-hooks/exhaustive-deps

  function goOlder() {
    const d = new Date(selectedDate + 'T00:00:00');
    d.setDate(d.getDate() - 1);
    setSelectedDate(toLocalISODate(d));
  }

  function goNewer() {
    const d = new Date(selectedDate + 'T00:00:00');
    d.setDate(d.getDate() + 1);
    setSelectedDate(toLocalISODate(d));
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

  // Fall back to first keyword so the "nothing selected" state is never shown while data exists
  const selectedKeyword =
    visibleKeywords?.find((kw) => kw.id === selectedKeywordId) ?? visibleKeywords?.[0] ?? null;

  if (isLoading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading…</p>
        </div>
      </div>
    );
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

  return (
    <div className="app">
      <header className="navbar">
        <div className="navbar__brand">
          <span className="navbar__title">Trend Engine</span>
          {isToday && !isSearchMode && <span className="live-badge">live</span>}
        </div>

        <form className="navbar__search" onSubmit={handleSearchSubmit}>
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

      <div className="app-body">
        <aside className="sidebar">
          <div className="sidebar__day-nav">
            <DayCycler
              label={formatDateLabel(selectedDate, today)}
              hasNewer={!isToday}
              hasOlder={true}
              onNewer={goNewer}
              onOlder={goOlder}
            />
          </div>

          <nav className="sidebar__keyword-list" aria-label="Keywords">
            {visibleKeywords?.map((kw) => (
              <button
                key={kw.id ?? kw.text}
                className={`keyword-item${selectedKeywordId === kw.id ? ' keyword-item--active' : ''}`}
                onClick={() => setSelectedKeywordId(kw.id)}
              >
                <span className="keyword-item__text">{kw.text}</span>
                <span className="keyword-item__count">{kw.articles.length}</span>
              </button>
            ))}
            {visibleKeywords?.length === 0 && (
              <p className="main-content__empty">No keywords for this day.</p>
            )}
          </nav>
        </aside>

        <main className="main-content">
          {isSearchMode ? (
            <SearchResults query={submittedQuery} results={searchResults} isLoading={isSearching} />
          ) : selectedKeyword ? (
            <div className="articles-list">
              {selectedKeyword.articles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>
          ) : (
            <p className="main-content__empty">Select a keyword to see articles.</p>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
