export interface Article {
  id: number;
  title: string | null;
  url: string | null;
  summary: string | null;
  image: string | null;
}

export interface ArticleSearchResult extends Article {
  distance: number;
}

export interface Keyword {
  id: number | null;
  text: string;
  articles: Article[];
}
