import { useEffect, useRef } from 'react';
import type { Keyword } from '../data-model/keyword';

const WS_URL = import.meta.env.VITE_API_BASE_URL
  .replace(/^https/, 'wss')
  .replace(/^http/, 'ws') + '/ws';

interface WsMessage {
  type: string;
  keywords: Keyword[];
}

export function useKeywordUpdates(onUpdate: (keywords: Keyword[]) => void) {
  const onUpdateRef = useRef(onUpdate);
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let closed = false;

    function connect() {
      ws = new WebSocket(WS_URL);

      ws.onmessage = (event: MessageEvent) => {
        const msg: WsMessage = JSON.parse(event.data);
        if (msg.type !== 'keywords_updated') return;
        onUpdateRef.current(msg.keywords);
      };

      ws.onclose = () => {
        if (closed) return;
        reconnectTimeout = setTimeout(connect, 3000);
      };
    }

    connect();

    return () => {
      // Prevent the pending onclose handler from scheduling a zombie reconnect.
      closed = true;
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, []);
}
