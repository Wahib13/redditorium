import { apiFetch } from './client';
import type { Keyword } from '../data-model/keyword';

export function fetchKeywords(date: string): Promise<Keyword[]> {
  return apiFetch<Keyword[]>(`/keywords/?date=${date}`);
}
