"use client";

import getMyChats from "../api/get_my_chats";
import { AuthRedirectError } from "@/lib/utils/errors";
import ErrorScreen from "@/components/error";
import LoadingScreen from "@/components/loading";
import { useQuery } from "@tanstack/react-query";

import ServerList from "./serverlist";

import { SIDEBAR_SETTINGS } from '@/settings/sidebar';

export default function ServerListWrapper({ children }: { children: React.ReactNode }) {
  const { data, error, isPending, isError } = useQuery({
    queryKey: [SIDEBAR_SETTINGS.QUERY_KEY],
    queryFn: getMyChats,
    
    staleTime: SIDEBAR_SETTINGS.QUERY_STALE_TIME,
    retry: (failureCount, err) => {
      if (err instanceof AuthRedirectError) return false; 
      return failureCount < SIDEBAR_SETTINGS.QUERY_N_RETRIES; 
    }
  });

  if (isPending) {
    return <LoadingScreen />;
  }

  if (isError) {
    return <ErrorScreen message={error?.message || 'Failed to load server list'} />;
  }
  
  return (
    <div className="fixed flex h-screen w-full">
      <ServerList chat_id_list={data} />
      {children}
    </div>
  )
}