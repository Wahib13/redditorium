import { useLayoutEffect, useRef, useState } from 'react';
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

  const hasSummary = !!article.summary;
  const isCollapsed = hasSummary && isTruncated && !expanded;

  return (
    <div className="article-card">
      {article.image && (
        <img
          className="article-card__image"
          src={article.image}
          alt=""
          loading="lazy"
        />
      )}
      <div className="article-card__body">
        <div className="article-card__title-row">
          <span className="article-card__title">{article.title ?? 'Untitled'}</span>
          {distance !== undefined && (
            <span className="article-card__distance" title="cosine distance (lower = closer match)">
              {distance.toFixed(3)}
            </span>
          )}
        </div>

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

        {hasSummary && (
          <div
            ref={summaryRef}
            className={`article-card__summary${isCollapsed ? ' article-card__summary--collapsed' : ''}`}
            dangerouslySetInnerHTML={{ __html: article.summary! }}
            onClick={isTruncated ? () => setExpanded((o) => !o) : undefined}
            role={isTruncated ? 'button' : undefined}
            tabIndex={isTruncated ? 0 : undefined}
            style={isTruncated ? { cursor: 'pointer' } : undefined}
          />
        )}

        {(!hasSummary || expanded || !isTruncated) && (
          <a
            href={article.url ?? '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="article-card__full-story"
            onClick={(e) => e.stopPropagation()}
          >
            Full story ↗
          </a>
        )}
      </div>
    </div>
  );
}
