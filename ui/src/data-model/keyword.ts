export interface Article {
  id: number;
  title: string | null;
  url: string | null;
  summary: string | null;
  image: string | null;
  keywords: { id: number; text: string }[];
  source_name: string | null;
  source_icon_url: string | null;
  created: string;
}

export interface ArticleSearchResult extends Article {
  distance: number;
}

export interface Keyword {
  id: number | null;
  text: string;
  articles: Article[];
}
