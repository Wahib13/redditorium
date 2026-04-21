import { useState } from 'react';
import type { Article, Keyword } from '../data-model/keyword';
import './KeywordCard.css';

interface Props {
  keyword: Keyword;
}

function ArticleRow({ article }: { article: Article }) {
  const [expanded, setExpanded] = useState(false);
  const hasSummary = !!article.summary;

  return (
    <li className="keyword-card__article">
      <button
        className={`keyword-card__article-row${hasSummary ? ' keyword-card__article-row--clickable' : ''}`}
        onClick={() => hasSummary && setExpanded((o) => !o)}
        aria-expanded={hasSummary ? expanded : undefined}
        disabled={!hasSummary}
      >
        <span className="keyword-card__title">{article.title ?? 'Untitled'}</span>
        {hasSummary && (
          <span className="keyword-card__chevron" aria-hidden="true">
            {expanded ? '▲' : '▼'}
          </span>
        )}
      </button>

      {expanded && (
        <div className="keyword-card__expanded">
          {hasSummary && (
            <div
              className="keyword-card__summary"
              dangerouslySetInnerHTML={{ __html: article.summary! }}
            />
          )}
          <a
            href={article.url ?? '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="keyword-card__full-story"
            onClick={(e) => e.stopPropagation()}
          >
            Full story ↗
          </a>
        </div>
      )}
    </li>
  );
}

export function KeywordCard({ keyword }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="keyword-card">
      <button
        className="keyword-card__header"
        onClick={() => setIsExpanded((e) => !e)}
        aria-expanded={isExpanded}
        aria-label={`${keyword.text}, ${keyword.articles.length} articles`}
      >
        <span className="keyword-card__text">{keyword.text}</span>
        <span className="keyword-card__count">{keyword.articles.length}</span>
        <span className="keyword-card__chevron" aria-hidden="true">
          {isExpanded ? '▲' : '▼'}
        </span>
      </button>

      {isExpanded && (
        <ul className="keyword-card__articles">
          {keyword.articles.map((article) => (
            <ArticleRow key={article.id} article={article} />
          ))}
        </ul>
      )}
    </div>
  );
}
