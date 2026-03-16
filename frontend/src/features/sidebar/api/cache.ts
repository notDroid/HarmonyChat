import { useQuery, queryOptions, QueryClient, useQueryClient } from '@tanstack/react-query';
import { SIDEBAR_SETTINGS } from '@/settings/sidebar';
import getMyChats from './get_my_chats';
import { ChatResponse } from '@/lib/api/model/chatResponse';
import { UserChatsResponse } from '@/lib/api/model/userChatsResponse';

export const sidebarQueryOptions = queryOptions({
  queryKey: [SIDEBAR_SETTINGS.QUERY_KEY],
  queryFn: getMyChats,
  staleTime: SIDEBAR_SETTINGS.QUERY_STALE_TIME,
});

export const prefetchSidebarChats = async (queryClient: QueryClient) => {
  return await queryClient.fetchQuery(sidebarQueryOptions);
};

export function useSidebarChats() {
  return useQuery(sidebarQueryOptions);
}

export function useChatMetadata(chat_id: string) {
  return useQuery({
    ...sidebarQueryOptions,
    // Select the metadata for the specific chat_id from the list of chats in the cache
    select: (chats) => chats?.find(c => c.chat_id === chat_id)?.meta
  });
}

export function useSidebarCache() {
  const queryClient = useQueryClient();
  const queryKey = sidebarQueryOptions.queryKey;

  const addChat = (newChat: ChatResponse) => {
    queryClient.setQueryData<UserChatsResponse['chats']>(queryKey, (oldChats) => {
      if (!oldChats) return oldChats;

      const newChatItem = {
        chat_id: newChat.chat_id,
        meta: newChat.meta
      };

      // Prepend the new chat to the list
      return [newChatItem, ...oldChats];
    });
  };

  const removeChat = (chat_id: string) => {
    queryClient.setQueryData<UserChatsResponse['chats']>(queryKey, (oldChats) => {
      if (!oldChats) return oldChats;
      return oldChats.filter(chat => chat.chat_id !== chat_id);
    });
  };

  return {
    addChat,
    removeChat
  };
}