import type { Article, ArticleSearchResult } from '../data-model/keyword';
import { ArticleRow } from './ArticleRow';
import './ArticleList.css';

interface Props {
  articles: (Article | ArticleSearchResult)[];
  hideKeyword?: string | null;
  onKeywordClick?: (text: string) => void;
}

/** A single bordered sheet of article rows separated by hairlines. */
export function ArticleList({ articles, hideKeyword, onKeywordClick }: Props) {
  return (
    <div className="article-list">
      {articles.map((article) => (
        <ArticleRow
          key={article.id}
          article={article}
          distance={'distance' in article ? article.distance : undefined}
          hideKeyword={hideKeyword}
          onKeywordClick={onKeywordClick}
        />
      ))}
    </div>
  );
}
