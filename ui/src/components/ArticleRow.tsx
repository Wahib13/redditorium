import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import DOMPurify from 'dompurify';
import type { Article } from '../data-model/keyword';
import { formatArticleTime } from '../lib/dates';
import { SourceAvatar } from './SourceAvatar';
import './ArticleRow.css';

interface Props {
  article: Article;
  /** Cosine distance from a search query; shown as a small badge when present. */
  distance?: number;
  /** Keyword already implied by the surrounding section; omitted from the meta line. */
  hideKeyword?: string | null;
  /** When given, only keywords it accepts are shown as labels (extracted phrases are hidden). */
  isTopic?: (text: string) => boolean;
  onKeywordClick?: (text: string) => void;
  /** When given, the source avatar and name link to that source's page. */
  onSourceClick?: (sourceName: string) => void;
}

export function ArticleRow({ article, distance, hideKeyword, isTopic, onKeywordClick, onSourceClick }: Props) {
  const [expanded, setExpanded] = useState(false);
  // Start true so the summary renders collapsed on first paint; useLayoutEffect corrects it before the browser paints.
  const [isTruncated, setIsTruncated] = useState(true);
  const summaryRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = summaryRef.current;
    if (!el) return;
    setIsTruncated(el.scrollHeight > el.clientHeight);
  }, [article.summary]);

  // Summaries come from feed-supplied HTML — sanitize before injecting.
  const safeSummary = useMemo(
    () => (article.summary ? DOMPurify.sanitize(article.summary) : ''),
    [article.summary],
  );
  const hasSummary = !!safeSummary;
  const isCollapsed = hasSummary && isTruncated && !expanded;
  const keywords = (article.keywords ?? []).filter((kw) => kw.text !== hideKeyword && (!isTopic || isTopic(kw.text)));
  const title = article.title ?? 'Untitled';
  const sourceName = article.source_name;
  const openSource = sourceName && onSourceClick ? () => onSourceClick(sourceName) : undefined;

  return (
    <article className="article-row">
      {sourceName &&
        (openSource ? (
          <button className="article-row__avatar" onClick={openSource} aria-label={`Articles from ${sourceName}`}>
            <SourceAvatar name={sourceName} iconUrl={article.source_icon_url} size="m" />
          </button>
        ) : (
          <div className="article-row__avatar">
            <SourceAvatar name={sourceName} iconUrl={article.source_icon_url} size="m" />
          </div>
        ))}

      <div className="article-row__body">
        <div className="article-row__meta">
          {sourceName &&
            (openSource ? (
              <button className="article-row__source" onClick={openSource}>
                {sourceName}
              </button>
            ) : (
              <span className="article-row__source">{sourceName}</span>
            ))}
          <time className="article-row__time" dateTime={article.created}>
            {formatArticleTime(article.created)}
          </time>
          {keywords.map((kw) =>
            onKeywordClick ? (
              <button
                key={kw.id ?? kw.text}
                className="article-row__keyword"
                onClick={() => onKeywordClick(kw.text)}
              >
                {kw.text}
              </button>
            ) : (
              <span key={kw.id ?? kw.text} className="article-row__keyword">
                {kw.text}
              </span>
            ),
          )}
          {distance !== undefined && (
            <span className="article-row__distance" title="Cosine distance (lower is a closer match)">
              {distance.toFixed(3)}
            </span>
          )}
        </div>

        <h3 className="article-row__title">
          {article.url ? (
            <a href={article.url} target="_blank" rel="noopener noreferrer">
              {title}
            </a>
          ) : (
            title
          )}
        </h3>

        {hasSummary && (
          <div
            ref={summaryRef}
            className={`article-row__summary${isCollapsed ? ' article-row__summary--collapsed' : ''}`}
            dangerouslySetInnerHTML={{ __html: safeSummary }}
          />
        )}

        {hasSummary && isTruncated && (
          <button
            className="article-row__toggle"
            onClick={() => setExpanded((o) => !o)}
            aria-expanded={expanded}
          >
            {expanded ? 'Show less' : 'Read more'}
          </button>
        )}
      </div>

      {article.image && (
        <a
          className="article-row__thumb-link"
          href={article.url ?? undefined}
          target="_blank"
          rel="noopener noreferrer"
          tabIndex={-1}
          aria-hidden="true"
        >
          <img className="article-row__thumb" src={article.image} alt="" loading="lazy" />
        </a>
      )}
    </article>
  );
}
