"use client";

import getMyChats from "../api/get_my_chats";
import { NetworkError, ApiError, AuthRedirectError } from "@/lib/utils/errors";
import ErrorScreen from "@/components/error";
import LoadingScreen from "@/components/loading";
import { useQuery } from "@tanstack/react-query";

import ServerList from "./serverlist";

export default function ServerListWrapper(
  { initial_chat_id_list, children }: 
  { initial_chat_id_list: string[] | undefined, children: React.ReactNode }
) {

  const { data, error, isLoading } = useQuery({
    queryKey: ['myChats'],
    queryFn: getMyChats,
    initialData: initial_chat_id_list, // Uses server-fetched data as fallback
    retry: (failureCount, err) => {
      if (err instanceof AuthRedirectError) return false; // Don't retry on auth errors
      return failureCount < 3; // Fallback to 3 retries for other errors
    }
  });

  if (!data && error) {
    if (error instanceof NetworkError) {
      return <LoadingScreen />;
    }
    return <ErrorScreen message={error.message || 'Failed to load server list'} />;
  }

  if (!data && isLoading) {
    return <LoadingScreen />;
  }
  
  return (
    <div className="fixed flex h-screen w-full">
      <ServerList chat_id_list={data || []} />
      {children}
    </div>
  )
}