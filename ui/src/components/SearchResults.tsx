import { useState } from 'react';
import type { ArticleSearchResult } from '../data-model/keyword';
import { ArticleCard } from './ArticleCard';
import { Pagination } from './Pagination';
import './SearchResults.css';

const PAGE_SIZE = 10;

interface Props {
  query: string;
  results: ArticleSearchResult[];
  isLoading: boolean;
  onClear: () => void;
  onKeywordClick?: (kwId: number) => void;
  selectedKeywordId?: number | null;
}

export function SearchResults({ query, results, isLoading, onClear, onKeywordClick, selectedKeywordId }: Props) {
  const [page, setPage] = useState(0);

  const totalPages = Math.ceil(results.length / PAGE_SIZE);
  const pageResults = results.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const hasNextPage = page + 1 < totalPages;

  return (
    <div className="search-view">
      <div className="search-view__header">
        <button className="search-view__back" onClick={onClear}>
          ← Back
        </button>
        <span className="search-view__meta">
          {isLoading
            ? 'Searching…'
            : `${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"`}
        </span>
      </div>

      {isLoading ? (
        <p className="search-view__status">Searching…</p>
      ) : results.length === 0 ? (
        <p className="search-view__status">No results for "{query}".</p>
      ) : (
        <>
          <div className="articles-list">
            {pageResults.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                distance={article.distance}
                onKeywordClick={onKeywordClick}
                selectedKeywordId={selectedKeywordId}
              />
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            hasNextPage={hasNextPage}
            onPrevious={() => setPage((p) => p - 1)}
            onNext={() => setPage((p) => p + 1)}
            isLoading={isLoading}
          />
        </>
      )}
    </div>
  );
}
