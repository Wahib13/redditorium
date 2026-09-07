import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { TopicTabs } from './components/TopicTabs';
import { Timelines, type TimelinesHandle } from './components/Timelines';
import { SearchResults } from './components/SearchResults';
import { useKeywordDays } from './hooks/useKeywordDays';
import { useKeywordUpdates } from './hooks/useKeywordUpdates';
import { useSearch } from './hooks/useSearch';
import type { ArticleSearchResult, Keyword } from './data-model/keyword';
import { shiftDate, utcISODate } from './lib/dates';
import './App.css';

/**
 * The topic timelines, in display order, as keyword `text` values (the feed topics from
 * seeds.yaml, lowercased). Hardcoded for now: the API mixes these with KeyBERT-extracted
 * keywords and does not say which is which, and how custom topics should behave is still open.
 */
const TOPICS = ['politics', 'technology', 'business', 'health'];
/** Days load one at a time as a timeline is scrolled, this many at a stretch before asking to continue. */
const AUTO_LOAD_DAYS = 14;

const isTopic = (text: string) => TOPICS.includes(text);

function App() {
  const queryClient = useQueryClient();

  // Recomputed on an interval so a tab left open past UTC midnight grows a new "Today" section.
  const [today, setToday] = useState(() => utcISODate(new Date()));
  useEffect(() => {
    const id = setInterval(() => setToday(utcISODate(new Date())), 60_000);
    return () => clearInterval(id);
  }, []);

  // The day list is shared by every topic timeline: today first, then one more day per load.
  const [dayCount, setDayCount] = useState(1);
  const [autoCap, setAutoCap] = useState(AUTO_LOAD_DAYS);
  const dates = useMemo(() => Array.from({ length: dayCount }, (_, i) => shiftDate(today, -i)), [today, dayCount]);
  const days = useKeywordDays(dates);

  // Live updates only ever touch today's query entry, so a past day can never be overwritten.
  const handleWsUpdate = useCallback(
    (keywords: Keyword[]) => queryClient.setQueryData(['keywords', utcISODate(new Date())], keywords),
    [queryClient],
  );
  useKeywordUpdates(handleWsUpdate);

  // The active timeline by keyword text; null = "All".
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const timelinesRef = useRef<TimelinesHandle>(null);

  const [inputValue, setInputValue] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);
  const { data: searchResults = [] as ArticleSearchResult[], isFetching: isSearching } = useSearch(submittedQuery);
  const isSearchMode = submittedQuery.trim().length > 0;

  const lastDay = days[days.length - 1];
  const isLoadingMore = lastDay?.isPending ?? false;
  // Pause on an error (the section offers Retry) and at the cap (the timeline offers "Show older days").
  const canLoadMore = dayCount < autoCap && !isLoadingMore && !(lastDay?.isError ?? false);
  const loadMore = useCallback(() => setDayCount((n) => Math.min(n + 1, autoCap)), [autoCap]);
  const showOlder = useCallback(() => setAutoCap((n) => n + AUTO_LOAD_DAYS), []);

  function selectTopic(topic: string | null) {
    if (topic === activeTopic) timelinesRef.current?.scrollToTop();
    else setActiveTopic(topic);
  }

  function clearSearch() {
    setInputValue('');
    setSubmittedQuery('');
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmittedQuery(inputValue.trim());
  }

  /** Topic labels in article rows (and search results) jump to that topic's timeline. */
  function openTopic(text: string) {
    if (!isTopic(text)) return;
    clearSearch();
    setActiveTopic(text);
  }

  function goHome(e: React.MouseEvent) {
    e.preventDefault();
    clearSearch();
    selectTopic(null);
  }

  return (
    <div className="app">
      <header className="chrome">
        <div className="chrome__row">
          <a className="brand" href="/" onClick={goHome}>
            <span className="brand__logo" aria-hidden="true">↗</span>
            <span className="brand__title">Trend Engine</span>
          </a>

          {!isSearchMode && <TopicTabs topics={TOPICS} active={activeTopic} onSelect={selectTopic} />}

          <form className="search" onSubmit={handleSearchSubmit} role="search">
            <svg className="search__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <line x1="16.5" y1="16.5" x2="21" y2="21" />
            </svg>
            <input
              ref={searchInputRef}
              className="search__input"
              type="search"
              placeholder="Search articles…"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
            {isSearchMode && (
              <button
                type="button"
                className="search__clear"
                onClick={() => {
                  clearSearch();
                  searchInputRef.current?.focus();
                }}
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
          </form>
        </div>
      </header>

      {isSearchMode ? (
        <main className="page">
          <div className="page__inner">
            <SearchResults
              key={submittedQuery}
              query={submittedQuery}
              results={searchResults}
              isLoading={isSearching}
              onClear={clearSearch}
              isTopic={isTopic}
              onKeywordClick={openTopic}
            />
          </div>
        </main>
      ) : (
        <Timelines
          ref={timelinesRef}
          topics={TOPICS}
          active={activeTopic}
          onActiveChange={setActiveTopic}
          days={days}
          today={today}
          canLoadMore={canLoadMore}
          onLoadMore={loadMore}
          onShowOlder={dayCount >= autoCap && !isLoadingMore ? showOlder : undefined}
          isTopic={isTopic}
          onKeywordClick={openTopic}
        />
      )}
    </div>
  );
}

export default App;
