import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Keyword } from '../data-model/keyword';

const WS_URL = import.meta.env.VITE_API_BASE_URL
  .replace(/^https/, 'wss')
  .replace(/^http/, 'ws') + '/ws';

interface WsMessage {
  type: string;
  keywords: Keyword[];
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
        if (msg.type !== 'keywords_updated') return;
        queryClient.setQueryData<Keyword[]>(['keywords', date], msg.keywords);
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
