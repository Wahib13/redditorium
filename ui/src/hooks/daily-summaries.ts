import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { getDailySummaries } from '../api/daily-summaries';

interface UseDailySummariesOptions {
  date?: string;
  topic_id?: number;
  skip?: number;
  limit?: number;
}

export function useDailySummaries(options?: UseDailySummariesOptions) {
  return useQuery({
    queryKey: ['daily-summaries', options?.date, options?.topic_id, options?.skip, options?.limit],
    queryFn: () => getDailySummaries(options),
    placeholderData: keepPreviousData,
  });
}
