export interface ArticleInKeyword {
  id: number;
  title: string | null;
  url: string | null;
}

export interface Keyword {
  id: number | null;
  text: string;
  articles: ArticleInKeyword[];
}
