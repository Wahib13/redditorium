import './DayCycler.css';

interface DayCyclerProps {
  label: string;
  hasNewer: boolean;
  hasOlder: boolean;
  onNewer: () => void;
  onOlder: () => void;
}

export function DayCycler({ label, hasNewer, hasOlder, onNewer, onOlder }: DayCyclerProps) {
  return (
    <nav className="day-cycler" aria-label="Day navigation">
      <button
        className="day-cycler-button"
        onClick={onNewer}
        disabled={!hasNewer}
        aria-label="Newer day"
      >
        ‹
      </button>
      <span className="day-cycler-label">{label}</span>
      <button
        className="day-cycler-button"
        onClick={onOlder}
        disabled={!hasOlder}
        aria-label="Older day"
      >
        ›
      </button>
    </nav>
  );
}
