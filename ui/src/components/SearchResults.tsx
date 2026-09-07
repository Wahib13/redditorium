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
  isTopic?: (text: string) => boolean;
  onKeywordClick?: (text: string) => void;
  onSourceClick?: (sourceName: string) => void;
}

/** Body of the search page; the input itself lives in the top bar (SearchBar). */
export function SearchResults({ query, results, isLoading, isTopic, onKeywordClick, onSourceClick }: Props) {
  const [page, setPage] = useState(0);

  if (!query) {
    return <p className="empty-state">Search every article by meaning: a topic, a place, a name.</p>;
  }

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
      </div>
    );
  }

  if (results.length === 0) {
    return <p className="empty-state">Nothing matched “{query}”.</p>;
  }

  const totalPages = Math.ceil(results.length / PAGE_SIZE);
  const pageResults = results.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <section className="search-results">
      <p className="search-results__count">
        {results.length} {results.length === 1 ? 'result' : 'results'} for “{query}”
      </p>
      <ArticleList articles={pageResults} isTopic={isTopic} onKeywordClick={onKeywordClick} onSourceClick={onSourceClick} />
      {totalPages > 1 && (
        <Pagination
          page={page}
          totalPages={totalPages}
          hasNextPage={page + 1 < totalPages}
          onPrevious={() => setPage((p) => p - 1)}
          onNext={() => setPage((p) => p + 1)}
          isLoading={isLoading}
        />
      )}
    </section>
  );
}
