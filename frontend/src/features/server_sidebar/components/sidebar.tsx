"use client";

import getMyChats from "../api/get_my_chats";

import { NetworkError, ApiError, AuthRedirectError } from "@/lib/api/errors";
import ErrorScreen from "@/components/error";
import LoadingScreen from "@/components/loading";
import useSWR from "swr";

import ServerList from "./serverlist";

export default function ServerListWrapper(
  { initial_chat_id_list, children }: 
  { initial_chat_id_list: string[] | undefined, children: React.ReactNode }
) {

  const { data, error, isLoading } = useSWR(
    '/api/user/me/chats', 
    getMyChats,
    { 
      fallbackData: initial_chat_id_list, 
      revalidateOnMount: initial_chat_id_list === undefined, // Only fetch if we didn't get data from server
      onErrorRetry: (error, key, config, revalidate, { retryCount }) => {
        if (error instanceof AuthRedirectError) return; // Don't retry on auth errors, just let the redirect happen
        // fallback to default retry logic for other errors
      }
    }
  );

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