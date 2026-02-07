import { useEffect, useMemo, useState } from 'react';
import { DailySummaryCard } from './components/DailySummaryCard';
import { DayCycler } from './components/DayCycler';
import { Pagination } from './components/Pagination';
import { useDailySummaries } from './hooks/daily-summaries';
import type { DailySummary } from './data-model/daily-summary';
import './App.css';

const PAGE_SIZE = 20;

function App() {
  const [dateIndex, setDateIndex] = useState(0);
  const [page, setPage] = useState(0);

  const { data: dailySummaries, isLoading, error } = useDailySummaries();

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const summaryDate = new Date(date);
    summaryDate.setHours(0, 0, 0, 0);

    if (summaryDate.getTime() === today.getTime()) {
      return 'Today';
    }

    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric'
    });
  };

  const summariesByDate = useMemo(() => {
    if (!dailySummaries || dailySummaries.length === 0) {
      return [];
    }

    // Group summaries by date
    const grouped = dailySummaries.reduce((acc, summary) => {
      const dateKey = summary.date;
      if (!acc[dateKey]) {
        acc[dateKey] = [];
      }
      acc[dateKey].push(summary);
      return acc;
    }, {} as Record<string, DailySummary[]>);

    // Convert to array and sort by date (most recent first)
    const sortedDates = Object.keys(grouped).sort((a, b) => {
      return new Date(b).getTime() - new Date(a).getTime();
    });

    return sortedDates.map(date => ({
      date,
      formattedDate: formatDate(date),
      summaries: grouped[date]
    }));
  }, [dailySummaries]);

  const currentDateGroup = summariesByDate[dateIndex];
  const allSummaries = currentDateGroup?.summaries ?? [];
  const totalPages = Math.ceil(allSummaries.length / PAGE_SIZE);
  const paginatedSummaries = allSummaries.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const showPagination = totalPages > 1;

  // Reset within-day page when switching dates
  useEffect(() => {
    setPage(0);
  }, [dateIndex]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [dateIndex, page]);

  if (isLoading) {
    return (
      <div className="app-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading news...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-container">
        <div className="error-container">
          <h2>Failed to load news</h2>
          <p>Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">Trend Engine</h1>
        <p className="app-subtitle">News Summary</p>
      </header>

      <main className="app-main">
        {summariesByDate.length === 0 ? (
          <div className="empty-state">
            <p>No summaries available.</p>
          </div>
        ) : (
          <>
            <DayCycler
              label={currentDateGroup.formattedDate}
              hasNewer={dateIndex > 0}
              hasOlder={dateIndex < summariesByDate.length - 1}
              onNewer={() => setDateIndex(i => i - 1)}
              onOlder={() => setDateIndex(i => i + 1)}
            />
            <div className="date-sections">
              <section className="date-section">
                <div className="summaries-grid">
                  {paginatedSummaries.map(summary => (
                    <DailySummaryCard key={summary.id} summary={summary} />
                  ))}
                </div>
              </section>
            </div>
            {showPagination && (
              <Pagination
                page={page}
                hasNextPage={page < totalPages - 1}
                onPrevious={() => setPage(p => p - 1)}
                onNext={() => setPage(p => p + 1)}
                isLoading={false}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App
