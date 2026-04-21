import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Keyword, Article } from '../data-model/keyword';

const WS_URL = import.meta.env.VITE_API_BASE_URL
  .replace(/^https/, 'wss')
  .replace(/^http/, 'ws') + '/ws';

interface WsArticle {
  id: number;
  title: string | null;
  url: string | null;
  summary: string | null;
  image: string | null;
  keywords: { id: number; text: string }[];
}

interface WsMessage {
  type: string;
  articles: WsArticle[];
}

export function useKeywordUpdates(date: string) {
  const queryClient = useQueryClient();

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(WS_URL);

      ws.onmessage = (event: MessageEvent) => {
        const msg: WsMessage = JSON.parse(event.data);
        if (msg.type !== 'articles_added') return;

        queryClient.setQueryData<Keyword[]>(['keywords', date], (prev) => {
          if (!prev) return prev;

          // shallow-clone the array and each keyword's articles list we may mutate
          const updated = prev.map((k) => ({ ...k, articles: [...k.articles] }));

          for (const article of msg.articles) {
            const newArticle: Article = {
              id: article.id,
              title: article.title,
              url: article.url,
              summary: article.summary ?? null,
              image: article.image ?? null,
            };
            for (const kw of article.keywords) {
              const existing = updated.find((k) => k.id === kw.id);
              if (existing) {
                if (!existing.articles.some((a) => a.id === article.id)) {
                  existing.articles.push(newArticle);
                }
              } else {
                updated.push({ id: kw.id, text: kw.text, articles: [newArticle] });
              }
            }
          }

          return updated;
        });
      };

      ws.onclose = () => {
        reconnectTimeout = setTimeout(connect, 3000);
      };
    }

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, [date, queryClient]);
}
