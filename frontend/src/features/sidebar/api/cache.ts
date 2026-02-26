import { useQuery, queryOptions, QueryClient } from '@tanstack/react-query';
import { SIDEBAR_SETTINGS } from '@/settings/sidebar';
import getMyChats from './get_my_chats';
import { ApiError, AuthRedirectError } from '@/lib/utils/errors';

export const sidebarQueryOptions = queryOptions({
  queryKey: [SIDEBAR_SETTINGS.QUERY_KEY],
  queryFn: getMyChats,
  staleTime: SIDEBAR_SETTINGS.QUERY_STALE_TIME,
  retry: (failureCount, err) => {
    if (err instanceof AuthRedirectError) return false; 
    if (err instanceof ApiError) return false;
    return failureCount < SIDEBAR_SETTINGS.QUERY_N_RETRIES; 
  }
});

export const prefetchSidebarChats = async (queryClient: QueryClient) => {
  return await queryClient.fetchQuery(sidebarQueryOptions);
};

export function useSidebarChats() {
  return useQuery(sidebarQueryOptions);
}