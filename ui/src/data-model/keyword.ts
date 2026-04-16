export interface ArticleInKeyword {
  id: number;
  title: string | null;
  url: string | null;
}

export interface Keyword {
  id: number;
  text: string;
  articles: ArticleInKeyword[];
}
