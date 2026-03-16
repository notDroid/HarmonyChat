"use client";
import { ChatHeader, ChatHeaderProps } from "../ui/header";
import { useChatMetadata } from "@/features/sidebar/api/cache";
import ChatHeaderSkeleton from "../ui/loading_header";
import ChatInfoMenu from "./info_menu"; 

export default function ChatHeaderComponent({ chat_id }: { chat_id: string }) {
  const { data: metadata, isLoading } = useChatMetadata(chat_id);

  if (isLoading) {
    return <ChatHeaderSkeleton />;
  }

  const headerMetadata: ChatHeaderProps = {
    title: metadata?.title || "Unknown Chat",
  };
  if (metadata?.description) {
    headerMetadata.description = metadata.description;
  }

  return (
    <ChatHeader metadata={headerMetadata}>
      <ChatInfoMenu chat_id={chat_id} />
    </ChatHeader>
  );
}