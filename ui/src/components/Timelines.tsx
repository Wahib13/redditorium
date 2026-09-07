import { useEffect, useImperativeHandle, useMemo, useRef, type Ref, type RefObject } from 'react';
import type { KeywordDay } from '../hooks/useKeywordDays';
import { DaySection } from './DaySection';
import './Timelines.css';

export interface TimelinesHandle {
  /** Scroll the active timeline back to today. */
  scrollToTop: () => void;
}

interface PanelProps {
  days: KeywordDay[];
  /** Restrict every timeline to one source (a source page); null = every source */
  source: string | null;
  today: string;
  isTopic: (text: string) => boolean;
  onKeywordClick: (text: string) => void;
  onSourceClick?: (sourceName: string) => void;
}

/**
 * Scroll-driven collapse of the profile header, shared by every panel. `progress` (0…1) moves
 * with the scroll *delta* of whichever panel is visible, so scrolling down shrinks the header
 * and scrolling up grows it again from anywhere, and swiping between panels never changes it.
 */
interface Collapse {
  /** Pixels of scrolling that take the header from fully shown to fully collapsed. */
  range: number;
  progressRef: RefObject<number>;
  onChange: (progress: number) => void;
}

interface Props extends PanelProps {
  ref?: Ref<TimelinesHandle>;
  /** Timeline 0 is "All"; timeline i + 1 is topics[i]. */
  topics: string[];
  /** null = "All" */
  active: string | null;
  onActiveChange: (topic: string | null) => void;
  /** Enables the collapsing header: how many px of scroll collapse it fully. */
  collapseRange?: number;
  /** Receives the collapse progress (0…1) whenever it changes. */
  onCollapseChange?: (progress: number) => void;
}

/**
 * Horizontal scroll-snap strip with one full-width panel per topic. Each panel is its own
 * vertical scroller through the shared list of days, so every topic keeps its own position.
 */
export function Timelines({ ref, topics, active, onActiveChange, collapseRange, onCollapseChange, ...panelProps }: Props) {
  const names: (string | null)[] = [null, ...topics];

  const progressRef = useRef(0);
  const collapse = useMemo<Collapse | undefined>(
    () => (collapseRange && onCollapseChange ? { range: collapseRange, progressRef, onChange: onCollapseChange } : undefined),
    [collapseRange, onCollapseChange],
  );
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

  // activeIndex changed from outside (tab, topic label, brand): bring the strip there.
  // Changes that came from a swipe were reported by handleScroll and need no scrolling.
  useEffect(() => {
    const el = scrollerRef.current;
    if (!el || reportedRef.current === activeIndex) return;
    const left = activeIndex * el.clientWidth;
    const smooth = mountedRef.current && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    mountedRef.current = true;
    // Already there (e.g. index 0 on mount): no scroll event will follow, so don't wait for one.
    if (Math.abs(el.scrollLeft - left) < 1) {
      reportedRef.current = activeIndex;
      return;
    }
    targetRef.current = activeIndex;
    el.scrollTo({ left, behavior: smooth ? 'smooth' : 'instant' });
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
        <Timeline key={topic ?? '\0all'} index={i} topic={topic} active={i === activeIndex} collapse={collapse} {...panelProps} />
      ))}
    </main>
  );
}

interface TimelineProps extends PanelProps {
  index: number;
  topic: string | null;
  active: boolean;
  collapse?: Collapse;
}

/** scrollTop clamped to the scrollable range, so overscroll bounce contributes no delta. */
function clampedTop(el: HTMLElement) {
  return Math.min(Math.max(el.scrollTop, 0), Math.max(el.scrollHeight - el.clientHeight, 0));
}

function Timeline({
  index,
  topic,
  active,
  days,
  source,
  today,
  isTopic,
  onKeywordClick,
  onSourceClick,
  collapse,
}: TimelineProps) {
  const rootRef = useRef<HTMLElement>(null);
  const lastTopRef = useRef(0);
  const allLoaded = days.every((day) => !day.isPending);

  // Becoming the visible panel: keep the header exactly where it is. A panel sitting nearer its
  // top than the header's collapse would allow is nudged down, so the content stays flush with
  // the header and there is room to scroll up and grow it back.
  useEffect(() => {
    if (!active) return;
    const el = rootRef.current;
    if (!el) return;
    if (collapse) {
      const wanted = collapse.progressRef.current * collapse.range;
      if (el.scrollTop < wanted) el.scrollTop = wanted;
    }
    lastTopRef.current = clampedTop(el);
  }, [active, collapse]);

  function handleScroll() {
    if (!active) return;
    const el = rootRef.current;
    if (!el) return;
    const top = clampedTop(el);
    const delta = top - lastTopRef.current;
    lastTopRef.current = top;
    if (!collapse || delta === 0) return;

    const { range, progressRef, onChange } = collapse;
    // Never more collapsed than the scroll position allows, so the content top stays flush with the header.
    const next = Math.min(Math.max(progressRef.current + delta / range, 0), 1, top / range);
    if (next === progressRef.current) return;
    progressRef.current = next;
    onChange(next);
  }

  return (
    <section
      ref={rootRef}
      className="timeline"
      role="tabpanel"
      id={`topic-panel-${index}`}
      aria-labelledby={`topic-tab-${index}`}
      tabIndex={active ? 0 : -1}
      inert={!active}
      onScroll={handleScroll}
    >
      <div className="timeline__inner">
        {days.map((day) => (
          <DaySection
            key={day.date}
            day={day}
            topic={topic}
            source={source}
            today={today}
            isTopic={isTopic}
            onKeywordClick={onKeywordClick}
            onSourceClick={onSourceClick}
          />
        ))}
        <div className="timeline__foot">
          {allLoaded && (
            <p className="timeline__caught-up">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="m8.5 12.5 2.5 2.5 4.5-5" />
              </svg>
              You’re all caught up
              <span className="timeline__caught-up-sub">
                That’s the last {days.length} {days.length === 1 ? 'day' : 'days'}
              </span>
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
