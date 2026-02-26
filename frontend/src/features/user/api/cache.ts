// frontend/src/features/user/api/cache.ts
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { USER_SETTINGS } from '@/settings/user';
import { getCurrentUserDetailsApiV1UsersMeGet } from '@/lib/api/user/user';
import { UserResponse as User } from '@/lib/api/model';

export function useUserCache() {
  const queryClient = useQueryClient();
  const queryKey = [USER_SETTINGS.QUERY_KEY];

  // 1. Hook for React Components to subscribe to user data
  const useCurrentUser = () => {
    return useQuery({
        queryKey: [USER_SETTINGS.QUERY_KEY],
        queryFn: async () => {
          const res = await getCurrentUserDetailsApiV1UsersMeGet();
          return res.data as User;
        },
        staleTime: USER_SETTINGS.QUERY_STALE_TIME, // Long time or Infinity to cache for the session
      });
  };

  // 2. Synchronous getter for non-reactive functions (like onMutate)
  const getCurrentUserSync = (): User | undefined => {
    return queryClient.getQueryData<User>(queryKey);
  };

  // 3. Setter for manually updating the cache (e.g., after a profile edit)
  const updateCurrentUser = (partialUser: Partial<User>) => {
    queryClient.setQueryData<User>(queryKey, (oldData) => {
      if (!oldData) return undefined;
      return { ...oldData, ...partialUser };
    });
  };

  return {
    useCurrentUser,
    getCurrentUserSync,
    updateCurrentUser,
    queryKey,
  };
}