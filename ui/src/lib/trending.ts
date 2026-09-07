// Trending-keyword ranking: which extracted keywords earn a timeline, and in what order.
// Deliberately a pure function over plain data so it can move to the API verbatim
// (see "Trending keywords" in CLAUDE.md).

import type { Keyword } from '../data-model/keyword';

export interface TrendingOptions {
  /** A keyword needs at least this many articles in the window (raw count, not decayed). */
  minArticles: number;
  /** An article's vote halves every this many hours. */
  halfLifeHours: number;
  /** Keyword texts never ranked (the fixed feed topics). */
  exclude?: readonly string[];
  /** Reference time for ages; defaults to the current time. */
  now?: number;
}

/** Article timestamps are naive UTC from the API. */
function ageHours(created: string, now: number): number {
  return Math.max(0, (now - Date.parse(created + 'Z')) / 3_600_000);
}

/**
 * Ranks keywords by a time-decayed article count: every article counts 0.5 ^ (age / half-life),
 * so a burst this morning outranks a larger total from two days ago, while a big story that ran
 * across the whole window still outranks a couple of fresh articles.
 *
 * `days` is the window's data as the API returns it, one `Keyword[]` per day; the same keyword
 * text appears once per day it has articles on.
 */
export function rankTrendingKeywords(days: (Keyword[] | undefined)[], options: TrendingOptions): string[] {
  const { minArticles, halfLifeHours, exclude = [], now = Date.now() } = options;
  const excluded = new Set(exclude);
  const stats = new Map<string, { count: number; score: number }>();

  for (const keywords of days) {
    for (const kw of keywords ?? []) {
      if (excluded.has(kw.text)) continue;
      const entry = stats.get(kw.text) ?? { count: 0, score: 0 };
      for (const article of kw.articles) {
        entry.count += 1;
        entry.score += Math.pow(0.5, ageHours(article.created, now) / halfLifeHours);
      }
      stats.set(kw.text, entry);
    }
  }

  return [...stats]
    .filter(([, s]) => s.count >= minArticles)
    .sort(([textA, a], [textB, b]) => b.score - a.score || textA.localeCompare(textB))
    .map(([text]) => text);
}
