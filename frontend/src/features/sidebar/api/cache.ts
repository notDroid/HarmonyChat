import { useQuery, queryOptions, QueryClient } from '@tanstack/react-query';
import { SIDEBAR_SETTINGS } from '@/settings/sidebar';
import getMyChats from './get_my_chats';

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