import { useCallback } from 'react';
import { useQueries, type UseQueryResult } from '@tanstack/react-query';
import { fetchKeywords } from '../api/keywords';
import type { Keyword } from '../data-model/keyword';

export interface KeywordDay {
  date: string;
  keywords: Keyword[] | undefined;
  isPending: boolean;
  isFetching: boolean;
  isError: boolean;
  refetch: () => void;
}

/**
 * One query per date, all keyed `['keywords', date]`. Every topic timeline reads the same
 * day objects, so a day is fetched once no matter how many timelines show it, and the
 * WebSocket handler can update today's entry through the query cache.
 */
export function useKeywordDays(dates: string[]): KeywordDay[] {
  const combine = useCallback(
    (results: UseQueryResult<Keyword[]>[]) =>
      results.map((r, i) => ({
        date: dates[i],
        keywords: r.data,
        isPending: r.isPending,
        isFetching: r.isFetching,
        isError: r.isError,
        refetch: () => {
          void r.refetch();
        },
      })),
    [dates],
  );

  return useQueries({
    queries: dates.map((date) => ({
      queryKey: ['keywords', date],
      queryFn: () => fetchKeywords(date),
      refetchOnWindowFocus: false,
      staleTime: 5 * 60_000,
    })),
    combine,
  });
}
