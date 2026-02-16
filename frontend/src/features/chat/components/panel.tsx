'use client';

import useSWR from 'swr';

import getChatHistory from "../api/get_chat_history";

import ChatPanel from "../ui/panel";
import LoadingChatPanel from "../ui/loading"

import { ChatMessage } from "@/lib/api/model";


export default function ChatPanelView(
  { chat_id, refreshInterval, initial_messages = [], loaded = false }: 
  { chat_id: string, refreshInterval: number, initial_messages: ChatMessage[], loaded: boolean }
) {
  // SWR Hook: Fetches chat history for the given chat_id
  const { data, isLoading } = useSWR(
    chat_id, 
    () => getChatHistory(chat_id),
    { refreshInterval: refreshInterval, fallbackData: initial_messages }
  )

  if (isLoading && !loaded) {
    return <LoadingChatPanel />;
  }

  return <ChatPanel messages={data} />;
}