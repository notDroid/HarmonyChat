import { useQueryClient, InfiniteData, useInfiniteQuery, infiniteQueryOptions, QueryClient } from '@tanstack/react-query';
import { CHAT_PANEL_SETTINGS } from '@/settings/chat_panel';
import { ChatHistoryResponse } from "@/lib/api/model";
import { UIMessage } from "../ui/message";

import getChatHistory from './get_chat_history';

export const chatHistoryQueryOptions = (chat_id: string) => infiniteQueryOptions({
  queryKey: [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id],
  queryFn: ({ pageParam }) => getChatHistory(chat_id, CHAT_PANEL_SETTINGS.PAGE_SIZE, pageParam),

  initialPageParam: undefined as string | undefined,
  getNextPageParam: (lastPage) => lastPage.next_cursor || undefined,
  refetchOnWindowFocus: false,
});

export function useChatHistory(chat_id: string) {
  return useInfiniteQuery(chatHistoryQueryOptions(chat_id));
}

export const prefetchChatHistory = async (queryClient: QueryClient, chat_id: string) => {
  return await queryClient.prefetchInfiniteQuery(chatHistoryQueryOptions(chat_id));
};

export function useChatCache(chat_id: string) {
  const queryClient = useQueryClient();
  const queryKey = [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id];

  const insertOrUpdateMessage = (newMessage: UIMessage) => {
    // If the cache is empty, we cannot safely append without breaking pagination.
    // In this case, we should invalidate the cache, which occurs when a websocket message arrives while we have no messages loaded.
    const currentData = queryClient.getQueryData<InfiniteData<ChatHistoryResponse>>(queryKey);
    if (!currentData || !currentData.pages || currentData.pages.length === 0) {
      console.log("[Cache] Deferring WS message and forcing refetch...");
      queryClient.invalidateQueries({ queryKey });
      return; 
    }

    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (oldData) => {
      if (!oldData) return oldData; // This should not happen due to the check above 

      let messageReplaced = false;
			
			// Try to find and replace the message in the existing pages
      const newPages = oldData.pages.map(page => {
        const updatedMessages = page.messages.map(msg => {
          const m = msg as UIMessage;
          
          if (m.ulid === newMessage.ulid || (m.client_uuid && m.client_uuid === newMessage.client_uuid)) {
            messageReplaced = true;
            return { ...m, ...newMessage, status: newMessage.status || 'sent' };
          }
          return m;
        });
        return { ...page, messages: updatedMessages };
      });
			
			// If the message wasn't found and replaced, it means it's a new message that should be added to the end of the first page
			// It will be sorted correctly later when we flatten and sort all messages
      if (!messageReplaced) {
        newPages[0] = {
          ...newPages[0],
          messages: [...newPages[0].messages, { ...newMessage, status: newMessage.status || 'sent' }]
        };
      }

      return { ...oldData, pages: newPages };
    });
  };

  const updateMessageStatus = (client_uuid: string, status: 'pending' | 'error' | 'sent') => {
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (oldData) => {
      if (!oldData) return oldData;

			// Update the status of the message with the matching client_uuid
      const newPages = oldData.pages.map(page => ({
        ...page,
        messages: page.messages.map(msg => {
          const m = msg as UIMessage;
          if (m.client_uuid === client_uuid) {
            return { ...m, status };
          }
          return m;
        })
      }));

      return { ...oldData, pages: newPages };
    });
  };

  const invalidateChatCache = () => {
    queryClient.invalidateQueries({ queryKey });
  }

  const snapshotChatCache = async () => {
    await queryClient.cancelQueries({ queryKey });
    return queryClient.getQueryData<InfiniteData<ChatHistoryResponse>>(queryKey);
  }

  return {
    insertOrUpdateMessage,
    updateMessageStatus,
    invalidateChatCache,
    snapshotChatCache,
  };
}