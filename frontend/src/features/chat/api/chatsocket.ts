// src/features/chat/api/chatsocket.ts
import { useCallback } from "react";
import { useChatEvents } from "./use_chat_events";
import { useChatCache } from "./cache";

export function useChatQuerySync(chat_id: string) {
  const { insertOrUpdateMessage, invalidateChatCache } = useChatCache(chat_id);

  const handleEvent = useCallback((event: any) => {
    console.log("Received chat event", event);
    insertOrUpdateMessage(event);
  }, [insertOrUpdateMessage]);

  useChatEvents(chat_id, handleEvent);
}