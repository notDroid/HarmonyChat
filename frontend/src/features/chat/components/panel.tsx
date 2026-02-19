'use client';

import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import getChatHistory from "../api/get_chat_history";
import { useChatSocket } from '../api/websocket';

import ChatPanel from "../ui/panel";
import LoadingChatPanel from "../ui/loading"

import { ChatMessage } from "@/lib/api/model";

export default function ChatPanelView(
  { chat_id, refreshInterval, initial_messages = [], loaded = false }: 
  { chat_id: string, refreshInterval: number, initial_messages: ChatMessage[], loaded: boolean }
) {
  const queryClient = useQueryClient();

  // React Query for initial fetch and persistence
  const { data, isLoading } = useQuery({
    queryKey: ['chatHistory', chat_id],
    queryFn: () => getChatHistory(chat_id),
    initialData: initial_messages,
    refetchOnWindowFocus: false, // matches revalidateOnFocus: false
  });

  // Define how to handle incoming WebSocket messages
  const handleNewMessage = useCallback((newMessage: ChatMessage) => {
    console.log("Received new message via WebSocket:", newMessage);
    
    // Mutate React Query cache locally to update UI immediately
    queryClient.setQueryData(['chatHistory', chat_id], (currentMessages: ChatMessage[] | undefined) => {
      if (!currentMessages) return [newMessage];
      
      // Prevent duplicates (in case REST and WS return same message)
      const exists = currentMessages.some(m => m.ulid === newMessage.ulid);
      if (exists) return currentMessages;

      // Append new message
      return [...currentMessages, newMessage];
    });
  }, [queryClient, chat_id]);

  // Connect the Socket
  useChatSocket(chat_id, handleNewMessage);

  if (isLoading && !loaded) {
    return <LoadingChatPanel />;
  }

  return <ChatPanel messages={data || []} />;
}