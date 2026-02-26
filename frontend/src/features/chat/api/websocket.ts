import useWebSocket from "react-use-websocket";
import { getWebSocketUrl } from "@/lib/api/ws/utils";
import { ChatMessage } from "@/lib/api/model";
import { CHAT_PANEL_SETTINGS } from '@/settings/chat_panel';

type OnMessageCallback = (message: ChatMessage) => void;
type OnConnectCallback = () => void;

export function useChatWebSocket(chat_id: string, onMessage: OnMessageCallback, onConnect?: OnConnectCallback) {
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
    onOpen: () => {
      console.log(`[WS] Connected to chat ${chat_id}`);
      if (onConnect) onConnect();
    },
    onClose: () => console.log(`[WS] Disconnected from chat ${chat_id}`),
    onError: (event) => console.error("[WS] Error", event),

    // Reconnection settings
    shouldReconnect: (closeEvent) => true,
    reconnectAttempts: 5,
    reconnectInterval: CHAT_PANEL_SETTINGS.WS_RECONNECT_INTERVAL_MS,
  });
}