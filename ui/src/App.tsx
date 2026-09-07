import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useLocation, useMatch, useNavigate, useSearchParams } from 'react-router-dom';
import { TopicTabs } from './components/TopicTabs';
import { Timelines, type TimelinesHandle } from './components/Timelines';
import { SearchBar } from './components/SearchBar';
import { SearchResults } from './components/SearchResults';
import { SourceAvatar } from './components/SourceAvatar';
import { useKeywordDays } from './hooks/useKeywordDays';
import { useKeywordUpdates } from './hooks/useKeywordUpdates';
import { useSearch } from './hooks/useSearch';
import type { ArticleSearchResult, Keyword } from './data-model/keyword';
import { shiftDate, utcISODate } from './lib/dates';
import { rankTrendingKeywords } from './lib/trending';
import './App.css';

/**
 * The topic timelines, in display order, as keyword `text` values (the feed topics from
 * seeds.yaml, lowercased). Hardcoded for now: the API mixes these with KeyBERT-extracted
 * keywords and does not say which is which, and how custom topics should behave is still open.
 */
const TOPICS = ['politics', 'technology', 'business', 'health'];
/**
 * The feed window: how many days each timeline shows, today included. All of them load up front,
 * the keyword tabs are decided from them once, and the feed ends with "all caught up" after the
 * last one. A candidate for a user setting later.
 */
const FEED_DAYS = 5;
/** Any other keyword with at least this many articles across the window gets a timeline after the topics. */
const MIN_KEYWORD_ARTICLES = 4;
/** Ranking those keywords: an article's vote halves every this many hours (see lib/trending.ts). */
const HALF_LIFE_HOURS = 24;
/** Top bar height. On Home the bar itself collapses, so this is also its collapse range. */
const HEADER_H = 52;
/** Height of the source page's profile header, which is also how many px of scrolling collapse it. */
const PROFILE_H = 84;

const BackIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m15 5-7 7 7 7" />
  </svg>
);

const SearchIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
    <circle cx="11" cy="11" r="7" />
    <line x1="16.5" y1="16.5" x2="21" y2="21" />
  </svg>
);

function App() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();

  // Routes: "/" is Home, "/source/:name" the same feed restricted to one source, "/search?q=" the search page.
  const source = useMatch('/source/:name')?.params.name ?? null;
  const isSearchPage = useMatch('/search') !== null;
  const [searchParams, setSearchParams] = useSearchParams();
  const query = isSearchPage ? (searchParams.get('q') ?? '').trim() : '';

  // Recomputed on an interval so a tab left open past UTC midnight grows a new "Today" section.
  const [today, setToday] = useState(() => utcISODate(new Date()));
  useEffect(() => {
    const id = setInterval(() => setToday(utcISODate(new Date())), 60_000);
    return () => clearInterval(id);
  }, []);

  // The window's days, newest first, shared by every topic timeline and fetched together.
  const dates = useMemo(() => Array.from({ length: FEED_DAYS }, (_, i) => shiftDate(today, -i)), [today]);
  const days = useKeywordDays(dates);

  // Live updates only ever touch today's query entry, so a past day can never be overwritten.
  const handleWsUpdate = useCallback(
    (keywords: Keyword[]) => queryClient.setQueryData(['keywords', utcISODate(new Date())], keywords),
    [queryClient],
  );
  useKeywordUpdates(handleWsUpdate);

  // Timelines: the fixed topics, then every other keyword with enough articles in the window,
  // ranked by recency-weighted count. Counted over all sources so Home and source pages share
  // one tab strip. The window is fixed and this only recomputes when the days' data changes
  // (initial load, a WebSocket push), so the strip never shifts while the user scrolls.
  const extraTopics = useMemo(
    () =>
      rankTrendingKeywords(
        days.map((day) => day.keywords),
        { minArticles: MIN_KEYWORD_ARTICLES, halfLifeHours: HALF_LIFE_HOURS, exclude: TOPICS },
      ),
    [days],
  );
  const topics = useMemo(() => [...TOPICS, ...extraTopics], [extraTopics]);
  const isTopic = useCallback((text: string) => topics.includes(text), [topics]);

  // The active timeline by keyword text; null = "All". Carries over between Home and source pages.
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const timelinesRef = useRef<TimelinesHandle>(null);

  // Part of the chrome shrinks in step with the scroll: the top bar on Home, the profile header
  // on a source page. The progress (0…1) is written straight to the --p custom property on .app;
  // App.css derives every size from it.
  const appRef = useRef<HTMLDivElement>(null);
  const setCollapse = useCallback((p: number) => {
    appRef.current?.style.setProperty('--p', p.toFixed(4));
  }, []);
  useEffect(() => {
    appRef.current?.style.setProperty('--p', '0');
  }, [source, isSearchPage]);

  const { data: searchResults = [] as ArticleSearchResult[], isFetching: isSearching } = useSearch(query);

  // The source page's logo comes from any loaded article of that source.
  const sourceIcon = useMemo(() => {
    if (source === null) return null;
    for (const day of days) {
      for (const kw of day.keywords ?? []) {
        const hit = kw.articles.find((a) => a.source_name === source);
        if (hit) return hit.source_icon_url;
      }
    }
    return null;
  }, [days, source]);

  function selectTopic(topic: string | null) {
    if (topic === activeTopic) timelinesRef.current?.scrollToTop();
    else setActiveTopic(topic);
  }

  /** Back arrow: the previous page when there is one in this session, else Home. */
  function goBack() {
    if (location.key !== 'default') navigate(-1);
    else navigate('/');
  }

  function goHome(e: React.MouseEvent) {
    e.preventDefault();
    selectTopic(null);
  }

  /** Topic labels in article rows jump to that topic's timeline (leaving the search page if needed). */
  function openTopic(text: string) {
    if (!isTopic(text)) return;
    setActiveTopic(text);
    if (isSearchPage) navigate('/');
  }

  /** Source avatars and names in article rows open that source's page; the current topic carries over. */
  function openSource(name: string) {
    navigate(`/source/${encodeURIComponent(name)}`);
  }

  const appClass = `app ${source !== null ? 'app--source' : isSearchPage ? 'app--search' : 'app--home'}`;
  const appVars = { '--header-h': `${HEADER_H}px`, '--profile-h': `${PROFILE_H}px` } as React.CSSProperties;

  return (
    <div className={appClass} ref={appRef} style={appVars}>
      <header className="chrome">
        <div className="topbar">
          <div className="topbar__side">
            {(source !== null || isSearchPage) && (
              <button className="icon-btn" onClick={goBack} aria-label="Back">
                <BackIcon />
              </button>
            )}
          </div>

          <div className="topbar__center">
            {isSearchPage ? (
              <SearchBar key={query} initial={query} onSubmit={(q) => setSearchParams(q ? { q } : {})} />
            ) : source !== null ? (
              <div className="topbar__profile" aria-hidden="true">
                <SourceAvatar name={source} iconUrl={sourceIcon} size="s" />
                <span className="topbar__profile-name">{source}</span>
              </div>
            ) : (
              <>
                <a className="brand" href="/" onClick={goHome}>
                  <span className="brand__logo" aria-hidden="true">↗</span>
                  <span className="brand__title">Trend Engine</span>
                </a>
                <button className="icon-btn" onClick={() => navigate('/search')} aria-label="Search">
                  <SearchIcon />
                </button>
              </>
            )}
          </div>

          <div className="topbar__side topbar__side--end">
            {source !== null && (
              <button className="icon-btn" onClick={() => navigate('/search')} aria-label="Search">
                <SearchIcon />
              </button>
            )}
          </div>
        </div>

        {source !== null && (
          <div className="profile">
            <div className="profile__inner">
              <h1 className="profile__name">{source}</h1>
              <SourceAvatar name={source} iconUrl={sourceIcon} size="l" />
            </div>
          </div>
        )}

        {!isSearchPage && <TopicTabs topics={topics} fixedCount={TOPICS.length} active={activeTopic} onSelect={selectTopic} />}
      </header>

      {isSearchPage ? (
        <main className="page">
          <div className="page__inner">
            <SearchResults
              key={query}
              query={query}
              results={searchResults}
              isLoading={isSearching}
              isTopic={isTopic}
              onKeywordClick={openTopic}
              onSourceClick={openSource}
            />
          </div>
        </main>
      ) : (
        <Timelines
          key={source ?? '\0home'}
          ref={timelinesRef}
          topics={topics}
          active={activeTopic}
          onActiveChange={setActiveTopic}
          days={days}
          source={source}
          today={today}
          isTopic={isTopic}
          onKeywordClick={openTopic}
          onSourceClick={source === null ? openSource : undefined}
          collapseRange={source !== null ? PROFILE_H : HEADER_H}
          onCollapseChange={setCollapse}
        />
      )}
    </div>
  );
}

export default App;
