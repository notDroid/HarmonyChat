'use client';

import { useCallback } from 'react';
import { useInfiniteQuery, useQueryClient, InfiniteData } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';

import getChatHistory from "../api/get_chat_history";
import { useChatSocket } from '../api/websocket';

import ChatPanel from "../ui/panel";
import LoadingChatPanel from "../ui/loading";

import { ChatMessage, ChatHistoryResponse } from "@/lib/api/model";
import { CHAT_PANEL_SETTINGS } from '@/settings/chat_panel';

export default function ChatPanelView(
  { chat_id }: 
  { chat_id: string }
) {
  const queryClient = useQueryClient();

  // Infinite Query for chat history with pagination
  const { 
    data, 
    isLoading, 
    fetchNextPage, 
    hasNextPage, 
    isFetchingNextPage 
  } = useInfiniteQuery({
    queryKey: [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id],
    queryFn: ({ pageParam }) => getChatHistory(chat_id, CHAT_PANEL_SETTINGS.PAGE_SIZE, pageParam),

    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor || undefined,

    refetchOnWindowFocus: false,
  });

  // Flatten pages and apply your sorting logic to ensure chronological order
  const messages = data?.pages.flatMap(page => page.messages) || [];
  const sortedMessages = [...messages].sort((a, b) => a.ulid.localeCompare(b.ulid));

  // Handler for incoming WebSocket messages
  const handleNewMessage = useCallback((newMessage: ChatMessage) => {
    console.log("Received new message via WebSocket:", newMessage);
    
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
      [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id], 
      (oldData) => {
        // If we don't have any data yet, we can't really insert the message, so we return the old data.
        if (!oldData) return oldData;
        
        // Check if message already exists across any page, to prevent duplicates
        const exists = oldData.pages.some(page => 
          page.messages.some(m => m.ulid === newMessage.ulid)
        );
        if (exists) return oldData;
        
        // Insert the new message into the most recent page (index 0)
        // It doesn't matter if it's out of order here, because sortedMessages handles the UI render order
        const newPages = [...oldData.pages];
        newPages[0] = {
          ...newPages[0],
          messages: [...newPages[0].messages, newMessage]
        };
        
        return { ...oldData, pages: newPages };
      }
    );
  }, [queryClient, chat_id]);

  useChatSocket(chat_id, handleNewMessage);

  // Observer for infinite scrolling - triggers fetchNextPage when the target comes into view
  const { ref: observerTarget } = useInView({
    threshold: 1.0,
    onChange: (inView) => {
      // If the target comes into view and we have more pages to load 
      // and we're not already loading, fetch the next page
      if (inView && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
  });

  if (isLoading) {
    return <LoadingChatPanel />;
  }

  return (
    <ChatPanel 
      messages={sortedMessages} 
      observerTarget={observerTarget}
      isFetchingNextPage={isFetchingNextPage}
    />
  );
}