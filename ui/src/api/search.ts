import { apiFetch } from './client';
import type { ArticleSearchResult } from '../data-model/keyword';

export function fetchSearchResults(q: string, limit = 50): Promise<ArticleSearchResult[]> {
  return apiFetch<ArticleSearchResult[]>(`/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}
