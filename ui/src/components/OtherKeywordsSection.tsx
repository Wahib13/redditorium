import { useState } from 'react';
import type { Keyword } from '../data-model/keyword';
import './OtherKeywordsSection.css';

interface Props {
  keywords: Keyword[];
  excludeArticleIds?: Set<number>;
}

export function OtherKeywordsSection({ keywords, excludeArticleIds }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (keywords.length === 0) return null;

  const uniqueArticles = Array.from(
    new Map(
      keywords.flatMap((kw) => kw.articles).map((a) => [a.id, a])
    ).values()
  ).filter((a) => !excludeArticleIds?.has(a.id));

  return (
    <div className="other-section">
      <button
        className="other-section__header"
        onClick={() => setIsExpanded((e) => !e)}
        aria-expanded={isExpanded}
        aria-label={`Other, ${uniqueArticles.length} articles`}
      >
        <span className="other-section__title">Other</span>
        <span className="other-section__meta">
          {uniqueArticles.length} articles
        </span>
        <span className="other-section__chevron" aria-hidden="true">
          {isExpanded ? '▲' : '▼'}
        </span>
      </button>

      {isExpanded && (
        <ul className="other-section__list">
          {uniqueArticles.map((article) => (
            <li key={article.id} className="other-section__item">
              <a
                href={article.url ?? '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="other-section__link"
              >
                {article.title ?? 'Untitled'}
                <span className="other-section__external" aria-hidden="true">↗</span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
