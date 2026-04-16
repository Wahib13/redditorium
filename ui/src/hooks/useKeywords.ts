import { useQuery } from '@tanstack/react-query';
import { fetchKeywords } from '../api/keywords';

export function useKeywords(date: string) {
  return useQuery({
    queryKey: ['keywords', date],
    queryFn: () => fetchKeywords(date),
  });
}
