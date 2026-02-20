'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useInfiniteQuery, useQueryClient, InfiniteData } from '@tanstack/react-query';

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
  const observerTarget = useRef<HTMLDivElement>(null);

  const { 
    data, 
    isLoading, 
    fetchNextPage, 
    hasNextPage, 
    isFetchingNextPage 
  } = useInfiniteQuery({
    queryKey: [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id],
    queryFn: ({ pageParam }) => getChatHistory(chat_id, 50, pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor || undefined,
    refetchOnWindowFocus: false,
  });

  // Flatten pages and apply your sorting logic to ensure chronological order
  const messages = data?.pages.flatMap(page => page.messages) || [];
  const sortedMessages = [...messages].sort((a, b) => a.ulid.localeCompare(b.ulid));

  const handleNewMessage = useCallback((newMessage: ChatMessage) => {
    console.log("Received new message via WebSocket:", newMessage);
    
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
      [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id], 
      (oldData) => {
        if (!oldData) return oldData;
        
        // Check if message already exists across any page
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

  // Intersection Observer for infinite scrolling
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 1.0 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

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