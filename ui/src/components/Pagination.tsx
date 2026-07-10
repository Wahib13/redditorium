import './Pagination.css';

interface PaginationProps {
  page: number;
  totalPages: number;
  hasNextPage: boolean;
  onPrevious: () => void;
  onNext: () => void;
  isLoading: boolean;
}

export function Pagination({ page, totalPages, hasNextPage, onPrevious, onNext, isLoading }: PaginationProps) {
  return (
    <nav className="pagination" aria-label="Pagination">
      <button
        className="pagination-button"
        onClick={onPrevious}
        disabled={page === 0 || isLoading}
      >
        Previous
      </button>
      <span className="pagination-info">Page {page + 1} / {totalPages}</span>
      <button
        className="pagination-button"
        onClick={onNext}
        disabled={!hasNextPage || isLoading}
      >
        Next
      </button>
    </nav>
  );
}
