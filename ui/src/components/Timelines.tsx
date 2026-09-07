import { useEffect, useImperativeHandle, useRef, type Ref } from 'react';
import type { KeywordDay } from '../hooks/useKeywordDays';
import { DaySection } from './DaySection';
import './Timelines.css';

export interface TimelinesHandle {
  /** Scroll the active timeline back to today. */
  scrollToTop: () => void;
}

interface Props {
  ref?: Ref<TimelinesHandle>;
  /** Timeline 0 is "All"; timeline i + 1 is topics[i]. */
  topics: string[];
  /** null = "All" */
  active: string | null;
  onActiveChange: (topic: string | null) => void;
  days: KeywordDay[];
  today: string;
  /** Whether the active timeline may request another day when its end scrolls into view. */
  canLoadMore: boolean;
  onLoadMore: () => void;
  /** Present when auto-loading has paused and the user must ask for older days. */
  onShowOlder?: () => void;
  isTopic: (text: string) => boolean;
  onKeywordClick: (text: string) => void;
}

/**
 * Horizontal scroll-snap strip with one full-width panel per topic. Each panel is its own
 * vertical scroller through the shared list of days, so every topic keeps its own position.
 */
export function Timelines({ ref, topics, active, onActiveChange, ...panelProps }: Props) {
  const names: (string | null)[] = [null, ...topics];
  // Falls back to "All" if the active topic is not (or no longer) in the list.
  const activeIndex = Math.max(0, names.indexOf(active));

  const scrollerRef = useRef<HTMLElement>(null);
  /** Index most recently derived from the scroll position (a swipe, or a finished programmatic scroll). */
  const reportedRef = useRef<number | null>(null);
  /** Destination of an in-flight programmatic scroll; intermediate panels it passes are not reported. */
  const targetRef = useRef<number | null>(null);
  const mountedRef = useRef(false);

  useImperativeHandle(
    ref,
    () => ({
      scrollToTop: () => {
        const panel = scrollerRef.current?.children[activeIndex] as HTMLElement | undefined;
        panel?.scrollTo({ top: 0, behavior: 'smooth' });
      },
    }),
    [activeIndex],
  );

  // activeIndex changed from outside (tab, topic label, brand, or the topic list growing
  // around the active topic): bring the strip there. Changes that came from a swipe were
  // reported by handleScroll and need no scrolling.
  useEffect(() => {
    const el = scrollerRef.current;
    if (!el || reportedRef.current === activeIndex) return;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    targetRef.current = activeIndex;
    el.scrollTo({ left: activeIndex * el.clientWidth, behavior: mountedRef.current && !reduceMotion ? 'smooth' : 'instant' });
    mountedRef.current = true;
  }, [activeIndex]);

  function handleScroll() {
    const el = scrollerRef.current;
    if (!el || el.clientWidth === 0) return;
    const index = Math.round(el.scrollLeft / el.clientWidth);
    if (targetRef.current !== null && index !== targetRef.current) return;
    targetRef.current = null;
    reportedRef.current = index;
    onActiveChange(names[index] ?? null);
  }

  // A user gesture takes over from any programmatic scroll still in flight.
  function cancelTarget() {
    targetRef.current = null;
  }

  return (
    <main
      className="timelines"
      ref={scrollerRef}
      onScroll={handleScroll}
      onWheel={cancelTarget}
      onTouchStart={cancelTarget}
      onPointerDown={cancelTarget}
    >
      {names.map((topic, i) => (
        <Timeline key={topic ?? '\0all'} index={i} topic={topic} active={i === activeIndex} {...panelProps} />
      ))}
    </main>
  );
}

interface TimelineProps {
  index: number;
  topic: string | null;
  active: boolean;
  days: KeywordDay[];
  today: string;
  canLoadMore: boolean;
  onLoadMore: () => void;
  onShowOlder?: () => void;
  isTopic: (text: string) => boolean;
  onKeywordClick: (text: string) => void;
}

function Timeline({ index, topic, active, days, today, canLoadMore, onLoadMore, onShowOlder, isTopic, onKeywordClick }: TimelineProps) {
  const rootRef = useRef<HTMLElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Only the visible timeline drives loading; the day list is shared, so the others follow.
  // The observer is rebuilt whenever loading finishes, which re-checks a still-visible sentinel.
  useEffect(() => {
    if (!active || !canLoadMore) return;
    const root = rootRef.current;
    const target = sentinelRef.current;
    if (!root || !target) return;

    let fired = false;
    const observer = new IntersectionObserver(
      (entries) => {
        if (fired || !entries.some((e) => e.isIntersecting)) return;
        fired = true;
        onLoadMore();
      },
      { root, rootMargin: '0px 0px 600px 0px' },
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [active, canLoadMore, onLoadMore]);

  return (
    <section
      ref={rootRef}
      className="timeline"
      role="tabpanel"
      id={`topic-panel-${index}`}
      aria-labelledby={`topic-tab-${index}`}
      tabIndex={active ? 0 : -1}
      inert={!active}
    >
      <div className="timeline__inner">
        {days.map((day) => (
          <DaySection key={day.date} day={day} topic={topic} today={today} isTopic={isTopic} onKeywordClick={onKeywordClick} />
        ))}
        <div className="timeline__foot" ref={sentinelRef}>
          {onShowOlder && (
            <button className="timeline__older" onClick={onShowOlder}>
              Show older days
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
