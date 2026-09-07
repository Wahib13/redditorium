import { useState } from 'react';
import './SearchBar.css';

interface Props {
  initial: string;
  onSubmit: (query: string) => void;
}

/** The search page's input, living in the top bar. Submits on Enter; the clear button empties the query. */
export function SearchBar({ initial, onSubmit }: Props) {
  const [value, setValue] = useState(initial);

  return (
    <form
      className="searchbar"
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(value.trim());
      }}
    >
      <svg className="searchbar__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <line x1="16.5" y1="16.5" x2="21" y2="21" />
      </svg>
      <input
        autoFocus
        className="searchbar__input"
        type="search"
        placeholder="Search articles"
        aria-label="Search articles"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      {value && (
        <button
          type="button"
          className="searchbar__clear"
          aria-label="Clear search"
          onClick={() => {
            setValue('');
            onSubmit('');
          }}
        >
          ✕
        </button>
      )}
    </form>
  );
}
