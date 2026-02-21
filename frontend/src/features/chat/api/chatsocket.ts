import { useCallback } from "react";
import { useQueryClient, InfiniteData } from "@tanstack/react-query";
import { useChatWebSocket } from "./websocket";
import { ChatMessage, ChatHistoryResponse } from "@/lib/api/model";
import { CHAT_PANEL_SETTINGS } from "@/settings/chat_panel";

export function useChatQuerySync(chat_id: string) {
  const queryClient = useQueryClient();

  // Create websocket callback
  const handleNewMessage = useCallback((newMessage: ChatMessage) => {
    console.log("[WS Sync] New message received:", newMessage);
    
    // Update chat state with new message (ensuring no duplicates)
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
      [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id], 
      (oldData) => {
        // Don't accept new messages if we don't the page loaded
        if (!oldData) return oldData;
        
        // Check for duplicates
        const exists = oldData.pages.some(page => 
          page.messages.some(m => m.ulid === newMessage.ulid)
        );
        
        if (exists) return oldData;
        
        // Insert new message into the first page, sort later
        const newPages = [...oldData.pages];
        newPages[0] = {
          ...newPages[0],
          messages: [...newPages[0].messages, newMessage]
        };
        
        return { ...oldData, pages: newPages };
      }
    );
  }, [queryClient, chat_id]);

  // Connect the transport layer to the data layer
  useChatWebSocket(chat_id, handleNewMessage);
}