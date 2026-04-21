import type { ArticleSearchResult } from '../data-model/keyword';
import { ArticleCard } from './ArticleCard';
import './SearchResults.css';

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
    <div className="articles-list">
      {results.map((article) => (
        <ArticleCard key={article.id} article={article} distance={article.distance} />
      ))}
    </div>
  );
}
