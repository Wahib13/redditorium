import type { Article } from '../data-model/keyword';
import './ArticleCard.css';

interface Props {
  article: Article;
  distance?: number;
}

export function ArticleCard({ article, distance }: Props) {
  return (
    <div className="article-card">
      {article.image && (
        <img
          className="article-card__image"
          src={article.image}
          alt=""
          loading="lazy"
        />
      )}
      <div className="article-card__body">
        <div className="article-card__title-row">
          <span className="article-card__title">{article.title ?? 'Untitled'}</span>
          {distance !== undefined && (
            <span className="article-card__distance" title="cosine distance (lower = closer match)">
              {distance.toFixed(3)}
            </span>
          )}
        </div>
        {article.summary && (
          <div
            className="article-card__summary"
            dangerouslySetInnerHTML={{ __html: article.summary }}
          />
        )}
        <a
          href={article.url ?? '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="article-card__full-story"
        >
          Full story ↗
        </a>
      </div>
    </div>
  );
}
