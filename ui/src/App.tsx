import { useEffect, useRef, useState } from 'react';
import { KeywordCard } from './components/KeywordCard';
import { OtherKeywordsSection } from './components/OtherKeywordsSection';
import { DayCycler } from './components/DayCycler';
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

  const [inputValue, setInputValue] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { data: keywords, isLoading, isError } = useKeywords(selectedDate);
  useKeywordUpdates(selectedDate);

  const { data: searchResults = [] as import('./data-model/keyword').ArticleSearchResult[], isFetching: isSearching } = useSearch(submittedQuery);

  const isSearchMode = submittedQuery.trim().length > 0;

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [selectedDate]);

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

  if (isLoading) {
    return (
      <div className="app-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="app-container">
        <div className="error-container">
          <h2>Failed to load keywords</h2>
          <p>Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-title-row">
          <h1 className="app-title">Trend Engine</h1>
          {isToday && !isSearchMode && <span className="live-badge">live</span>}
        </div>

        <form className="search-form" onSubmit={handleSearchSubmit}>
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

      <main className="app-main">
        {isSearchMode ? (
          <SearchResults query={submittedQuery} results={searchResults} isLoading={isSearching} />
        ) : (
          <>
            <DayCycler
              label={formatDateLabel(selectedDate, today)}
              hasNewer={!isToday}
              hasOlder={true}
              onNewer={goNewer}
              onOlder={goOlder}
            />

            {keywords && keywords.length === 0 ? (
              <div className="empty-state">
                <p>No keywords for this day.</p>
              </div>
            ) : (() => {
              const main = keywords?.filter((kw) => kw.articles.length >= 2) ?? [];
              const other = keywords?.filter((kw) => kw.articles.length < 2) ?? [];
              const mainArticleIds = new Set(main.flatMap((kw) => kw.articles.map((a) => a.id)));
              return (
                <div className="keywords-grid">
                  {main.map((kw) => (
                    <KeywordCard key={kw.text} keyword={kw} />
                  ))}
                  <OtherKeywordsSection keywords={other} excludeArticleIds={mainArticleIds} />
                </div>
              );
            })()}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
