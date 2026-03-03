// src/features/chat/api/chatsocket.ts
import { useCallback } from "react";
import { useChatEvents } from "./use_chat_events";
import { useChatCache } from "./cache";
import { ChatEvent } from "@/features/websocket/model";

export function useChatQuerySync(chat_id: string) {
  const { insertOrUpdateMessage, invalidateChatCache } = useChatCache(chat_id);

  const handleEvent = useCallback((event: ChatEvent) => {
    console.log("Received chat event", event);
    switch (event.type) {
      case 'chat_message':
        insertOrUpdateMessage(event.payload);
        break;
      case 'chat_deleted':
        // Handle kicking the user out of the view or showing a modal
        break;
      case 'user_joined':
        // Update a member list cache
        break;
      default:
        console.warn('Unknown event type', event);
    }
  }, [insertOrUpdateMessage]);

  useChatEvents(chat_id, handleEvent);
}