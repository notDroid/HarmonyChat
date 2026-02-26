import { useCallback } from "react";
import { useChatWebSocket } from "./websocket";
import { ChatMessage } from "@/lib/api/model";
import { useChatCache } from "./cache";
import { UIMessage } from "../ui/message";

// This hook is responsible for syncing incoming WebSocket messages with the React Query cache
export function useChatQuerySync(chat_id: string) {
  const { insertOrUpdateMessage, queryKey, queryClient } = useChatCache(chat_id);

  const handleNewMessage = useCallback((newMessage: ChatMessage) => {
    insertOrUpdateMessage(newMessage as UIMessage);
  }, [insertOrUpdateMessage]);

  const handleConnect = useCallback(() => {
    queryClient.invalidateQueries({ queryKey });
  }, [queryClient, queryKey]);

  useChatWebSocket(chat_id, handleNewMessage, handleConnect);
}