import { useCallback } from "react";
import { useQueryClient, InfiniteData } from "@tanstack/react-query";
import { useChatWebSocket } from "./websocket";
import { ChatMessage, ChatHistoryResponse } from "@/lib/api/model"; 
import { CHAT_PANEL_SETTINGS } from "@/settings/chat_panel"; 
import { insertOrUpdateMessage } from "./utils";
import { UIMessage } from "../ui/message";

// Custom hook to sync WebSocket messages with the React Query cache for a specific chat
export function useChatQuerySync(chat_id: string) { 
  const queryClient = useQueryClient(); 

  const handleNewMessage = useCallback((newMessage: ChatMessage) => { 
    // When a new message is received via WebSocket insert it into the screen
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>( 
      [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id],  
      (oldData) => insertOrUpdateMessage(oldData, newMessage as UIMessage) 
    );
  }, [queryClient, chat_id]);

  // Set up the WebSocket connection and listen for new messages
  useChatWebSocket(chat_id, handleNewMessage);
}