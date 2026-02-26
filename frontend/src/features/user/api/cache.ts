import getCurrentUser from './get_user';
import { USER_SETTINGS } from '@/settings/user';
import { UserResponse as User } from '@/lib/api/model';
import { QueryClient, useQuery, useQueryClient } from '@tanstack/react-query';

export const userQueryOptions = {
  queryKey: [USER_SETTINGS.QUERY_KEY],
  queryFn: async () => await getCurrentUser(),
  staleTime: USER_SETTINGS.QUERY_STALE_TIME, 
};

export const prefetchCurrentUser = async (queryClient: QueryClient) => {
  return await queryClient.fetchQuery(userQueryOptions);
};

export function useUserCache() {
  const queryClient = useQueryClient();

  const useCurrentUser = () => useQuery(userQueryOptions);

  const getCurrentUser = async (): Promise<User> => {
    return await queryClient.ensureQueryData(userQueryOptions);
  };

  const updateCurrentUser = (partialUser: Partial<User>) => {
    queryClient.setQueryData<User>(userQueryOptions.queryKey, (oldData) => {
      if (!oldData) return undefined;
      return { ...oldData, ...partialUser };
    });
  };

  const clearUserCache = () => {
    queryClient.removeQueries({ queryKey: userQueryOptions.queryKey });
  };

  return {
    useCurrentUser,
    getCurrentUser,
    updateCurrentUser,
    clearUserCache,
  };
}