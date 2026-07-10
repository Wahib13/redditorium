import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import DOMPurify from 'dompurify';
import type { Article } from '../data-model/keyword';
import './ArticleCard.css';

interface Props {
  article: Article;
  distance?: number;
  onKeywordClick?: (kwId: number) => void;
  selectedKeywordId?: number | null;
}

export function ArticleCard({ article, distance, onKeywordClick, selectedKeywordId }: Props) {
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

  return (
    <article className="article-card">
      <div className="article-card__body">
        <div className="article-card__meta">
          {article.source_icon_url && (
            <img className="article-card__source-icon" src={article.source_icon_url} alt="" />
          )}
          {article.source_name && (
            <span className="article-card__source-name">{article.source_name}</span>
          )}
          {article.source_name && <span className="article-card__meta-sep">·</span>}
          <time className="article-card__created" dateTime={article.created}>
            {new Date(article.created + 'Z').toLocaleString('en-GB', {
              day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
            })}
          </time>
          {distance !== undefined && (
            <span className="article-card__distance" title="cosine distance (lower = closer match)">
              {distance.toFixed(3)}
            </span>
          )}
        </div>

        <h3 className="article-card__title">{article.title ?? 'Untitled'}</h3>

        {hasSummary && (
          <div
            ref={summaryRef}
            className={`article-card__summary${isCollapsed ? ' article-card__summary--collapsed' : ''}`}
            dangerouslySetInnerHTML={{ __html: safeSummary }}
            onClick={isTruncated ? () => setExpanded((o) => !o) : undefined}
            role={isTruncated ? 'button' : undefined}
            tabIndex={isTruncated ? 0 : undefined}
            style={isTruncated ? { cursor: 'pointer' } : undefined}
          />
        )}

        <div className="article-card__footer">
          {(article.keywords?.length ?? 0) > 0 && (
            <div className="article-card__keywords">
              {article.keywords.map((kw) => {
                const isActive = selectedKeywordId !== undefined && kw.id === selectedKeywordId;
                const activeClass = isActive ? ' article-card__keyword-tag--active' : '';
                return onKeywordClick ? (
                  <button
                    key={kw.id ?? kw.text}
                    className={`article-card__keyword-tag article-card__keyword-tag--clickable${activeClass}`}
                    onClick={(e) => { e.stopPropagation(); onKeywordClick(kw.id); }}
                  >
                    {kw.text}
                  </button>
                ) : (
                  <span key={kw.id ?? kw.text} className={`article-card__keyword-tag${activeClass}`}>
                    {kw.text}
                  </span>
                );
              })}
            </div>
          )}

          {(!hasSummary || expanded || !isTruncated) && (
            <a
              href={article.url ?? '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="article-card__full-story"
              onClick={(e) => e.stopPropagation()}
            >
              Full story
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M7 17 17 7" />
                <path d="M9 7h8v8" />
              </svg>
            </a>
          )}
        </div>
      </div>

      {article.image && (
        <img
          className="article-card__image"
          src={article.image}
          alt=""
          loading="lazy"
        />
      )}
    </article>
  );
}
