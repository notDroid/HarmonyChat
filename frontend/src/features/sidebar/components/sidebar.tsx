"use client";

import LoadingScreen from "@/components/loading";

import ServerList from "./serverlist";

import { useSidebarChats } from "../api/cache";

export default function ServerListWrapper({ children }: { children: React.ReactNode }) {
  const { data, error, isPending, isError } = useSidebarChats();

  if (isPending) {
    return <LoadingScreen />;
  }

  if (isError) {
    throw error;
  }
  
  return (
    <div className="fixed flex h-screen w-full">
      <ServerList chat_id_list={data} />
      {children}
    </div>
  );
}