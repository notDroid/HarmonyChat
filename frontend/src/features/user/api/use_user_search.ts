import { useQuery } from '@tanstack/react-query';
import { searchUsersByEmail } from './get_user';

export function useUserSearch(searchTerm: string) {
  return useQuery({
    queryKey: ['userSearch', searchTerm],
    queryFn: () => searchUsersByEmail(searchTerm),
    enabled: searchTerm.trim().length >= 2, // Only search if the term has at least 2 characters
    staleTime: 1000 * 60, // 1 minute
  });
}