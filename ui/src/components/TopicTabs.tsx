import { useEffect, useRef } from 'react';
import './TopicTabs.css';

interface Props {
  topics: string[];
  /** null = "All" */
  active: string | null;
  onSelect: (topic: string | null) => void;
}

/**
 * Tab 0 is the merged "All" feed; tab i + 1 is topics[i].
 * Tab and panel ids (`topic-tab-N` / `topic-panel-N`) follow the same numbering in Timelines.tsx.
 */
export function TopicTabs({ topics, active, onSelect }: Props) {
  const listRef = useRef<HTMLDivElement>(null);
  const values: (string | null)[] = [null, ...topics];
  const activeIndex = Math.max(0, values.indexOf(active));

  // Keep the active tab in view when the list overflows (mobile).
  useEffect(() => {
    listRef.current?.children[activeIndex]?.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
  }, [activeIndex]);

  function handleKeyDown(e: React.KeyboardEvent) {
    const delta = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
    if (delta === 0) return;
    e.preventDefault();
    const next = (activeIndex + delta + values.length) % values.length;
    onSelect(values[next]);
    (listRef.current?.children[next] as HTMLElement | undefined)?.focus();
  }

  return (
    <nav className="topic-tabs" aria-label="Topics">
      <div className="topic-tabs__list" role="tablist" ref={listRef} onKeyDown={handleKeyDown}>
        {values.map((topic, i) => (
          <button
            key={topic ?? '\0all'}
            role="tab"
            id={`topic-tab-${i}`}
            aria-controls={`topic-panel-${i}`}
            aria-selected={i === activeIndex}
            tabIndex={i === activeIndex ? 0 : -1}
            className={`topic-tab${i === activeIndex ? ' topic-tab--active' : ''}`}
            onClick={() => onSelect(topic)}
          >
            {topic ?? 'All'}
          </button>
        ))}
      </div>
    </nav>
  );
}
