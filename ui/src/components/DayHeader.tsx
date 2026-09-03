import './DayHeader.css';

interface Props {
  title: string;
  subtitle: string;
  isLive: boolean;
  hasNewer: boolean;
  onNewer: () => void;
  onOlder: () => void;
}

export function DayHeader({ title, subtitle, isLive, hasNewer, onNewer, onOlder }: Props) {
  return (
    <section className="day-header">
      <div className="day-header__text">
        <h1 className="day-header__title">
          {title}
          {isLive && (
            <span className="live-badge">
              <span className="live-badge__dot" />
              Live
            </span>
          )}
        </h1>
        <p className="day-header__subtitle">{subtitle}</p>
      </div>

      <nav className="day-header__nav" aria-label="Day navigation">
        <button className="day-header__btn" onClick={onOlder} aria-label="Previous day">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="m15 6-6 6 6 6" />
          </svg>
        </button>
        <button className="day-header__btn" onClick={onNewer} disabled={!hasNewer} aria-label="Next day">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="m9 6 6 6-6 6" />
          </svg>
        </button>
      </nav>
    </section>
  );
}
