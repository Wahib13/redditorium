import { useState } from 'react';
import type { Keyword } from '../data-model/keyword';
import './OtherKeywordsSection.css';

interface Props {
  keywords: Keyword[];
}

export function OtherKeywordsSection({ keywords }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (keywords.length === 0) return null;

  const totalArticles = keywords.reduce((sum, kw) => sum + kw.articles.length, 0);

  return (
    <div className="other-section">
      <button
        className="other-section__header"
        onClick={() => setIsExpanded((e) => !e)}
        aria-expanded={isExpanded}
        aria-label={`Other, ${keywords.length} keywords`}
      >
        <span className="other-section__title">Other</span>
        <span className="other-section__meta">
          {keywords.length} keywords · {totalArticles} articles
        </span>
        <span className="other-section__chevron" aria-hidden="true">
          {isExpanded ? '▲' : '▼'}
        </span>
      </button>

      {isExpanded && (
        <ul className="other-section__list">
          {keywords.map((kw) => (
            <li key={kw.id} className="other-section__item">
              <span className="other-section__keyword">{kw.text}</span>
              {kw.articles.map((article) => (
                <a
                  key={article.id}
                  href={article.url ?? '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="other-section__link"
                >
                  {article.title ?? 'Untitled'}
                  <span className="other-section__external" aria-hidden="true">↗</span>
                </a>
              ))}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
