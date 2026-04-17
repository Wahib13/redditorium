import { useEffect, useState } from 'react';
import { KeywordCard } from './components/KeywordCard';
import { OtherKeywordsSection } from './components/OtherKeywordsSection';
import { DayCycler } from './components/DayCycler';
import { useKeywords } from './hooks/useKeywords';
import { useKeywordUpdates } from './hooks/useKeywordUpdates';
import './App.css';

function toLocalISODate(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatDateLabel(dateStr: string, todayStr: string): string {
  if (dateStr === todayStr) return 'Today';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}

const today = toLocalISODate(new Date());

function App() {
  const [selectedDate, setSelectedDate] = useState(today);
  const isToday = selectedDate === today;

  const { data: keywords, isLoading, isError } = useKeywords(selectedDate);
  useKeywordUpdates(selectedDate);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [selectedDate]);

  function goOlder() {
    const d = new Date(selectedDate + 'T00:00:00');
    d.setDate(d.getDate() - 1);
    setSelectedDate(toLocalISODate(d));
  }

  function goNewer() {
    const d = new Date(selectedDate + 'T00:00:00');
    d.setDate(d.getDate() + 1);
    setSelectedDate(toLocalISODate(d));
  }

  if (isLoading) {
    return (
      <div className="app-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="app-container">
        <div className="error-container">
          <h2>Failed to load keywords</h2>
          <p>Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-title-row">
          <h1 className="app-title">Trend Engine</h1>
          {isToday && <span className="live-badge">live</span>}
        </div>
      </header>

      <main className="app-main">
        <DayCycler
          label={formatDateLabel(selectedDate, today)}
          hasNewer={!isToday}
          hasOlder={true}
          onNewer={goNewer}
          onOlder={goOlder}
        />

        {keywords && keywords.length === 0 ? (
          <div className="empty-state">
            <p>No keywords for this day.</p>
          </div>
        ) : (() => {
          const main = keywords?.filter((kw) => kw.articles.length >= 2) ?? [];
          const other = keywords?.filter((kw) => kw.articles.length < 2) ?? [];
          return (
            <div className="keywords-grid">
              {main.map((kw) => (
                <KeywordCard key={kw.text} keyword={kw} />
              ))}
              <OtherKeywordsSection keywords={other} />
            </div>
          );
        })()}
      </main>
    </div>
  );
}

export default App;
