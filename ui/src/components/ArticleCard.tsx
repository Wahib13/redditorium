import { useLayoutEffect, useRef, useState } from 'react';
import type { Article } from '../data-model/keyword';
import './ArticleCard.css';

interface Props {
  article: Article;
  distance?: number;
}

export function ArticleCard({ article, distance }: Props) {
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
