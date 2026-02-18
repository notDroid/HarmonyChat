import { useEffect, useRef } from "react";
import { getWebSocketUrl } from "@/lib/api/ws/utils";
import { ChatMessage } from "@/lib/api/model";

type OnMessageCallback = (message: ChatMessage) => void;

export function useChatSocket(chat_id: string, onMessage: OnMessageCallback) {
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 1. Construct URL
    const url = getWebSocketUrl(chat_id);

    // 2. Initialize Connection
    const ws = new WebSocket(url);
    socketRef.current = ws;

    // 3. Event Handlers
    ws.onopen = () => {
      console.log(`[WS] Connected to chat ${chat_id}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // We assume the backend sends a JSON object matching ChatMessage
        onMessage(data);
      } catch (err) {
        console.error("[WS] Failed to parse message", err);
      }
    };

    ws.onerror = (error) => {
      console.error("[WS] Error", error);
    };

    ws.onclose = () => {
      console.log(`[WS] Disconnected from chat ${chat_id}`);
    };

    // 4. Cleanup on Unmount or chat_id change
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [chat_id, onMessage]);
}