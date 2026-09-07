import { useState } from 'react';
import type { ArticleSearchResult } from '../data-model/keyword';
import { ArticleList } from './ArticleList';
import { Pagination } from './Pagination';
import './SearchResults.css';

const PAGE_SIZE = 10;

interface Props {
  query: string;
  results: ArticleSearchResult[];
  isLoading: boolean;
  onClear: () => void;
  isTopic?: (text: string) => boolean;
  onKeywordClick?: (text: string) => void;
}

export function SearchResults({ query, results, isLoading, onClear, isTopic, onKeywordClick }: Props) {
  const [page, setPage] = useState(0);

  const totalPages = Math.ceil(results.length / PAGE_SIZE);
  const pageResults = results.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const hasNextPage = page + 1 < totalPages;

  return (
    <section className="search-view">
      <div className="search-view__head">
        <button className="search-view__back" onClick={onClear}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="m15 6-6 6 6 6" />
          </svg>
          Back
        </button>
        <div className="search-view__text">
          <h1 className="search-view__title">“{query}”</h1>
          <p className="search-view__count">
            {isLoading
              ? 'Searching…'
              : `${results.length} result${results.length !== 1 ? 's' : ''}`}
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="loading-container loading-container--inline">
          <div className="loading-spinner" />
        </div>
      ) : results.length === 0 ? (
        <p className="empty-state">Nothing matched “{query}”.</p>
      ) : (
        <>
          <ArticleList articles={pageResults} isTopic={isTopic} onKeywordClick={onKeywordClick} />
          {totalPages > 1 && (
            <Pagination
              page={page}
              totalPages={totalPages}
              hasNextPage={hasNextPage}
              onPrevious={() => setPage((p) => p - 1)}
              onNext={() => setPage((p) => p + 1)}
              isLoading={isLoading}
            />
          )}
        </>
      )}
    </section>
  );
}
