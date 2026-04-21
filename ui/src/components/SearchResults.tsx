import { useState } from 'react';
import type { ArticleSearchResult } from '../data-model/keyword';
import './SearchResults.css';

function SearchResultRow({ article }: { article: ArticleSearchResult }) {
  const [expanded, setExpanded] = useState(false);
  const hasSummary = !!article.summary;

  return (
    <li className="search-result">
      <button
        className={`search-result__row${hasSummary ? ' search-result__row--clickable' : ''}`}
        onClick={() => hasSummary && setExpanded((o) => !o)}
        aria-expanded={hasSummary ? expanded : undefined}
        disabled={!hasSummary}
      >
        <span className="search-result__title">{article.title ?? 'Untitled'}</span>
        <span className="search-result__distance" title="cosine distance (lower = closer match)">
          {article.distance.toFixed(3)}
        </span>
        {hasSummary && (
          <span className="search-result__chevron" aria-hidden="true">
            {expanded ? '▲' : '▼'}
          </span>
        )}
      </button>

      {expanded && (
        <div className="search-result__expanded">
          {hasSummary && (
            <div
              className="search-result__summary"
              dangerouslySetInnerHTML={{ __html: article.summary! }}
            />
          )}
          <a
            href={article.url ?? '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="search-result__full-story"
            onClick={(e) => e.stopPropagation()}
          >
            Full story ↗
          </a>
        </div>
      )}
    </li>
  );
}

interface Props {
  query: string;
  results: ArticleSearchResult[];
  isLoading: boolean;
}

export function SearchResults({ query, results, isLoading }: Props) {
  if (isLoading) {
    return <p className="search-results__status">Searching…</p>;
  }

  if (results.length === 0) {
    return <p className="search-results__status">No results for "{query}".</p>;
  }

  return (
    <ul className="search-results__list">
      {results.map((article) => (
        <SearchResultRow key={article.id} article={article} />
      ))}
    </ul>
  );
}
