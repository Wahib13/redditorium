import { useState } from 'react';
import type { Keyword } from '../data-model/keyword';
import { ArticleCard } from './ArticleCard';
import './KeywordCard.css';

interface Props {
  keyword: Keyword;
}

export function KeywordCard({ keyword }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="keyword-card">
      <button
        className="keyword-card__header"
        onClick={() => setIsExpanded((e) => !e)}
        aria-expanded={isExpanded}
        aria-label={`${keyword.text}, ${keyword.articles.length} articles`}
      >
        <span className="keyword-card__text">{keyword.text}</span>
        <span className="keyword-card__count">{keyword.articles.length}</span>
        <span className="keyword-card__chevron" aria-hidden="true">
          {isExpanded ? '▲' : '▼'}
        </span>
      </button>

      {isExpanded && (
        <div className="keyword-card__articles">
          {keyword.articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
