import { useMutation, useQueryClient, InfiniteData } from '@tanstack/react-query';
import { CHAT_PANEL_SETTINGS } from '@/settings/chat_panel';
import { ChatHistoryResponse } from '@/lib/api/model';
import { sendMessageApiV1ChatsChatIdPost } from '@/lib/api/chat/chat';

import { UIMessage } from '../ui/message';

export default function useSendMessage(chat_id: string) {
  const queryClient = useQueryClient();
  const queryKey = [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id];

  return useMutation({
    mutationFn: async (content: string) => {
      // 2. Call the API directly from the client. 
      // This goes to your /api/proxy route, bypassing the Next.js Server Action queue.
      const result = await sendMessageApiV1ChatsChatIdPost(chat_id, { content });
      
      // 3. Orval returns the parsed JSON body directly on the .data property
      return result.data; 
    },
    
    // 1. Optimistic Update (Waiting State)
    onMutate: async (newContent) => {
      // Cancel any outgoing refetches to avoid overwriting our optimistic update
      await queryClient.cancelQueries({ queryKey });

      // Snapshot the previous value
      const previousData = queryClient.getQueryData<InfiniteData<ChatHistoryResponse>>(queryKey);

      // Create an optimistic message
      const tempId = `temp-${Date.now()}`;
      const optimisticMessage: UIMessage = {
        chat_id,
        content: newContent,
        ulid: tempId, // Fake ULID ensures it sorts to the bottom
        tempId,
        timestamp: new Date().toISOString(),
        user_id: "me", // Ideally, pull the actual current user's ID
        status: 'pending'
      };

      // Optimistically update the cache
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (old) => {
        if (!old) return old;
        const newPages = [...old.pages];
        newPages[0] = {
          ...newPages[0],
          messages: [...newPages[0].messages, optimisticMessage]
        };
        return { ...old, pages: newPages };
      });

      return { previousData, tempId };
    },

    // 2. Error State
    onError: (err, newContent, context) => {
      // Find the optimistic message and mark it as 'error' instead of rolling back completely
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (old) => {
        if (!old) return context?.previousData;
        
        const newPages = old.pages.map(page => ({
          ...page,
          messages: page.messages.map(msg => 
            (msg as UIMessage).tempId === context?.tempId 
              ? { ...msg, status: 'error' as const } 
              : msg
          )
        }));
        return { ...old, pages: newPages };
      });
    },

    // 3. Success State
    onSuccess: (realMessage, variables, context) => {
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (old) => {
        if (!old) return old;

        // Check if the WebSocket already delivered the real message while we were waiting
        const realMessageExists = old.pages.some(page => 
          page.messages.some(m => m.ulid === realMessage.ulid)
        );

        const newPages = old.pages.map(page => ({
          ...page,
          messages: page.messages
            // If the WS beat us to it, just erase the optimistic UI duplicate
            .filter(msg => !(realMessageExists && (msg as UIMessage).tempId === context?.tempId))
            // Otherwise, swap the optimistic message out for the real one
            .map(msg => 
              (!realMessageExists && (msg as UIMessage).tempId === context?.tempId) 
                ? realMessage 
                : msg
            )
        }));
        
        return { ...old, pages: newPages };
      });
    }
  });
}