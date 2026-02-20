'use client';

import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import getChatHistory from "../api/get_chat_history";
import { useChatSocket } from '../api/websocket';

import ChatPanel from "../ui/panel";
import LoadingChatPanel from "../ui/loading"

import { ChatMessage } from "@/lib/api/model";

export default function ChatPanelView(
  { chat_id }: 
  { chat_id: string }
) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['chatHistory', chat_id],
    queryFn: () => getChatHistory(chat_id),
    refetchOnWindowFocus: false,
  });

  const handleNewMessage = useCallback((newMessage: ChatMessage) => {
    console.log("Received new message via WebSocket:", newMessage);
    
    queryClient.setQueryData(['chatHistory', chat_id], (currentMessages: ChatMessage[] | undefined) => {
      if (!currentMessages) return [newMessage];
      
      const exists = currentMessages.some(m => m.ulid === newMessage.ulid);
      if (exists) return currentMessages;
      
      // Insert the new message and sort by ULID to maintain chronological order
      const updatedMessages = [...currentMessages, newMessage];
      return updatedMessages.sort((a, b) => a.ulid.localeCompare(b.ulid));
    });
  }, [queryClient, chat_id]);

  useChatSocket(chat_id, handleNewMessage);

  if (isLoading) {
    return <LoadingChatPanel />;
  }

  return <ChatPanel messages={data || []} />;
}