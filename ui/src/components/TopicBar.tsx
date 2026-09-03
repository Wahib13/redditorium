import './TopicBar.css';

export interface TopicTab {
  text: string;
  count: number;
}

export interface SourceOption {
  name: string;
  icon_url: string | null;
}

interface Props {
  tabs: TopicTab[];
  allCount: number;
  selected: string | null; // null = all topics
  onSelect: (text: string | null) => void;
  sources: SourceOption[];
  selectedSource: string | null;
  onSelectSource: (name: string | null) => void;
}

export function TopicBar({ tabs, allCount, selected, onSelect, sources, selectedSource, onSelectSource }: Props) {
  return (
    <div className="topic-bar">
      <div className="topic-bar__tabs" role="tablist" aria-label="Topics">
        <button
          role="tab"
          aria-selected={selected === null}
          className={`topic-tab${selected === null ? ' topic-tab--active' : ''}`}
          onClick={() => onSelect(null)}
        >
          All
          <span className="topic-tab__count">{allCount}</span>
        </button>
        {tabs.map((tab) => (
          <button
            key={tab.text}
            role="tab"
            aria-selected={selected === tab.text}
            className={`topic-tab${selected === tab.text ? ' topic-tab--active' : ''}${tab.count === 0 ? ' topic-tab--empty' : ''}`}
            onClick={() => onSelect(tab.text)}
          >
            {tab.text}
            <span className="topic-tab__count">{tab.count}</span>
          </button>
        ))}
      </div>

      {sources.length > 1 && (
        <div className="source-toggle" role="group" aria-label="Source">
          <button
            className={`source-toggle__btn${selectedSource === null ? ' source-toggle__btn--active' : ''}`}
            onClick={() => onSelectSource(null)}
          >
            All
          </button>
          {sources.map((src) => (
            <button
              key={src.name}
              title={src.name}
              className={`source-toggle__btn${selectedSource === src.name ? ' source-toggle__btn--active' : ''}`}
              onClick={() => onSelectSource(selectedSource === src.name ? null : src.name)}
            >
              {src.icon_url && <img className="source-toggle__icon" src={src.icon_url} alt="" />}
              <span className="source-toggle__label">{src.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
