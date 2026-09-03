// The server buckets articles by the UTC calendar day (see api.keywords.utc_today),
// so the frontend must reason about "today" and date navigation in UTC too.

export function utcISODate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function shiftDate(dateStr: string, deltaDays: number): string {
  const d = new Date(dateStr + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + deltaDays);
  return utcISODate(d);
}

function utcDate(dateStr: string): Date {
  return new Date(dateStr + 'T00:00:00Z');
}

/** Big heading for a day: "Today", "Yesterday", or "September 1" (with year if not this year). */
export function dayTitle(dateStr: string, todayStr: string): string {
  if (dateStr === todayStr) return 'Today';
  if (dateStr === shiftDate(todayStr, -1)) return 'Yesterday';
  const d = utcDate(dateStr);
  const sameYear = dateStr.slice(0, 4) === todayStr.slice(0, 4);
  return d.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
    timeZone: 'UTC',
  });
}

/** Secondary line under the heading: the part of the date the title didn't say. */
export function daySubtitle(dateStr: string, todayStr: string): string {
  const d = utcDate(dateStr);
  const isRecent = dateStr === todayStr || dateStr === shiftDate(todayStr, -1);
  return d.toLocaleDateString('en-US', {
    weekday: 'long',
    ...(isRecent ? { month: 'long', day: 'numeric' } : {}),
    timeZone: 'UTC',
  });
}

/** Article timestamps are naive UTC from the API; render in the viewer's local time. */
export function formatArticleTime(created: string): string {
  const d = new Date(created + 'Z');
  const isToday = utcISODate(d) === utcISODate(new Date());
  return d.toLocaleString('en-GB', {
    ...(isToday ? {} : { day: 'numeric', month: 'short' }),
    hour: '2-digit',
    minute: '2-digit',
  });
}
