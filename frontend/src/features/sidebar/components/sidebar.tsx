"use client";

import { AuthRedirectError } from "@/lib/utils/errors";
import ErrorScreen from "@/components/error";
import LoadingScreen from "@/components/loading";
import { NetworkError, ApiError } from "@/lib/utils/errors";

import ServerList from "./serverlist";

import { useSidebarChats } from "../api/cache";

export default function ServerListWrapper({ children }: { children: React.ReactNode }) {
  const { data, error, isPending, isError } = useSidebarChats();

  if (isPending) {
    return <LoadingScreen />;
  }

  if (isError) {
    if (error instanceof NetworkError) {
      return <ErrorScreen message={ error?.message || 'Unable to connect. Check your internet.'} />;
    }
    if (error instanceof ApiError) {
      return <ErrorScreen message={ error?.message || 'Unable to load chats.'} />;
    }
    if (error instanceof AuthRedirectError) {
      return <ErrorScreen message={ error?.message || 'Authentication error. Please log in again.'} />;
    }
    return <ErrorScreen message={error?.message || 'Failed to load server list'} />;
  }
  
  return (
    <div className="fixed flex h-screen w-full">
      <ServerList chat_id_list={data} />
      {children}
    </div>
  )
}