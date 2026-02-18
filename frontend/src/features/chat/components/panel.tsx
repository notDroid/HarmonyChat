'use client';

import { useCallback } from 'react';
import useSWR from 'swr';

import getChatHistory from "../api/get_chat_history";
import { useChatSocket } from '../api/websocket';

import ChatPanel from "../ui/panel";
import LoadingChatPanel from "../ui/loading"

import { ChatMessage, ChatHistoryResponse } from "@/lib/api/model";

export default function ChatPanelView(
  { chat_id, refreshInterval, initial_messages = [], loaded = false }: 
  { chat_id: string, refreshInterval: number, initial_messages: ChatMessage[], loaded: boolean }
) {
  // SWR for initial fetch and persistence
  const { data, isLoading, mutate } = useSWR(
    chat_id, 
    () => getChatHistory(chat_id),
    { 
      fallbackData: initial_messages,
      revalidateOnFocus: false, 
    }
  );

  // Define how to handle incoming WebSocket messages
  const handleNewMessage = useCallback((newMessage: ChatMessage) => {
    // Mutate SWR cache locally to update UI immediately
    console.log("Received new message via WebSocket:", newMessage);
    mutate((currentMessages: ChatMessage[] | undefined) => {
      if (!currentMessages) return [newMessage];
      
      // Prevent duplicates (in case REST and WS return same message)
      const exists = currentMessages.some(m => m.ulid === newMessage.ulid);
      if (exists) return currentMessages;

      // Append new message
      return [...currentMessages, newMessage];
    }, false); // false = do not trigger a re-fetch from API
  }, [mutate]);

  // Connect the Socket
  useChatSocket(chat_id, handleNewMessage);

  if (isLoading && !loaded) {
    return <LoadingChatPanel />;
  }

  return <ChatPanel messages={data || []} />;
}