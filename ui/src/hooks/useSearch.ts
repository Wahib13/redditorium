import { useQuery } from '@tanstack/react-query';
import type { ArticleSearchResult } from '../data-model/keyword';
import { fetchSearchResults } from '../api/search';

export function useSearch(query: string) {
  return useQuery<ArticleSearchResult[]>({
    queryKey: ['search', query],
    queryFn: () => fetchSearchResults(query),
    enabled: query.trim().length > 0,
    staleTime: 30_000,
  });
}
