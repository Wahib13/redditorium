import { useMemo } from 'react';
import type { Article, Keyword } from '../data-model/keyword';
import type { KeywordDay } from '../hooks/useKeywordDays';
import { dayTitle, daySubtitle } from '../lib/dates';
import { ArticleList } from './ArticleList';
import './DaySection.css';

interface Props {
  day: KeywordDay;
  /** null = the merged "All" timeline */
  topic: string | null;
  /** Restrict to one source (a source page); null = every source */
  source: string | null;
  today: string;
  /** Which keywords have a timeline; only those are shown as labels on rows. */
  isTopic: (text: string) => boolean;
  onKeywordClick: (text: string) => void;
  onSourceClick?: (sourceName: string) => void;
}

/** One day inside a topic timeline: a sticky date header and that day's articles for the topic. */
export function DaySection({ day, topic, source, today, isTopic, onKeywordClick, onSourceClick }: Props) {
  const articles = useMemo(() => articlesFor(day.keywords, topic, source), [day.keywords, topic, source]);
  const isToday = day.date === today;
  const title = dayTitle(day.date, today);
  const showSkeleton = day.isPending || (day.isError && day.isFetching);

  return (
    <section className="day" aria-label={title}>
      <header className="day__header">
        <h2 className="day__title">{title}</h2>
        <span className="day__subtitle">{daySubtitle(day.date, today)}</span>
        <span className="day__meta">
          {day.keywords && (
            <span className="day__count">
              {articles.length} {articles.length === 1 ? 'article' : 'articles'}
            </span>
          )}
          {isToday && (
            <span className="live-badge">
              <span className="live-badge__dot" />
              Live
            </span>
          )}
        </span>
      </header>

      <div className="day__body">
        {showSkeleton ? (
          <Skeleton />
        ) : day.isError ? (
          <p className="day__note">
            Couldn’t load this day.{' '}
            <button className="day__retry" onClick={day.refetch}>
              Retry
            </button>
          </p>
        ) : articles.length === 0 ? (
          <p className="day__note">
            No {topic && <span className="day__topic">{topic} </span>}articles{source && ` from ${source}`}.
          </p>
        ) : (
          <ArticleList articles={articles} hideKeyword={topic} isTopic={isTopic} onKeywordClick={onKeywordClick} onSourceClick={onSourceClick} />
        )}
      </div>
    </section>
  );
}

/**
 * A topic's articles for the day, or every article of the day (deduplicated, newest first)
 * for "All", optionally restricted to one source.
 */
function articlesFor(keywords: Keyword[] | undefined, topic: string | null, source: string | null): Article[] {
  if (!keywords) return [];
  const fromSource = (a: Article) => source === null || a.source_name === source;
  if (topic !== null) return (keywords.find((kw) => kw.text === topic)?.articles ?? []).filter(fromSource);

  const byId = new Map<number, Article>();
  for (const kw of keywords) {
    for (const a of kw.articles) {
      if (fromSource(a) && !byId.has(a.id)) byId.set(a.id, a);
    }
  }
  return [...byId.values()].sort((a, b) => (a.created < b.created ? 1 : a.created > b.created ? -1 : 0));
}

function Skeleton() {
  return (
    <div className="skeleton" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <div className="skeleton__row" key={i}>
          <span className="skeleton__line" style={{ width: '28%' }} />
          <span className="skeleton__line skeleton__line--title" style={{ width: '82%' }} />
          <span className="skeleton__line" style={{ width: '64%' }} />
        </div>
      ))}
    </div>
  );
}
