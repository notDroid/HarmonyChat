import useWebSocket from "react-use-websocket";
import { getWebSocketUrl } from "@/lib/api/ws/utils";
import { ChatMessage } from "@/lib/api/model";

type OnMessageCallback = (message: ChatMessage) => void;

export function useChatWebSocket(chat_id: string, onMessage: OnMessageCallback) {
  const url = getWebSocketUrl(chat_id);

  useWebSocket(url, {
    // Handle incoming messages
    onMessage: (event) => {
      try {
        const data: ChatMessage = JSON.parse(event.data);
        onMessage(data);
      } catch (err) {
        console.error("[WS] Failed to parse message", err);
      }
    },
    
    // Log connection status for debugging
    onOpen: () => console.log(`[WS] Connected to chat ${chat_id}`),
    onClose: () => console.log(`[WS] Disconnected from chat ${chat_id}`),
    onError: (event) => console.error("[WS] Error", event),

    // Reconnection settings
    shouldReconnect: (closeEvent) => true,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
  });
}