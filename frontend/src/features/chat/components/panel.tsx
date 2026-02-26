'use client';

import { useInView } from 'react-intersection-observer';

import { useChatQuerySync } from '../api/chatsocket';
import useSendMessage from "../api/use_send_message";

import ChatPanel from "../ui/panel";
import LoadingChatPanel from "../ui/loading";
import { UIMessage } from '../ui/message';

import { useChatHistory } from '../api/cache';

export default function ChatPanelComponent(
  { chat_id }: 
  { chat_id: string }
) {

  // Infinite Query for chat history with pagination
  const { 
    data, 
    isLoading, 
    fetchNextPage, 
    hasNextPage, 
    isFetchingNextPage,
    isError,
    error,

  } = useChatHistory(chat_id);

  // Flatten pages and apply your sorting logic to ensure chronological order
  const messages = data?.pages.flatMap(page => page.messages) || [];
  const sortedMessages = [...messages].sort((a, b) => {
    const timeA = new Date(a.timestamp).getTime();
    const timeB = new Date(b.timestamp).getTime();
    
    if (timeA === timeB) {
      return a.ulid.localeCompare(b.ulid);
    }
    return timeA - timeB;
  });

  // Sync WebSocket messages with the query cache
  useChatQuerySync(chat_id);

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

  // Retry logic for failed messages
  const { mutate: retrySend } = useSendMessage(chat_id);
  const handleRetry = (msg: UIMessage) => {
    retrySend({ content: msg.content, client_uuid: msg.client_uuid! });
  };

  if (isLoading) {
    return <LoadingChatPanel />;
  }

  if (isError) {
    throw error;
  }

  return (
    <ChatPanel 
      messages={sortedMessages} 
      observerTarget={observerTarget}
      isFetchingNextPage={isFetchingNextPage}
      onRetry={handleRetry}
    />
  );
}