'use client';

import { use } from 'react';
import useSWR from 'swr';
import Message from "@/components/ui/message"
import ChatBar from "@/components/ui/chat_bar"
import { getChatHistory, sendMessage} from "@/lib/api";
import LoadingChatPanel from "@/components/ui/loading_chat_panel"

// Temporary constants for demo purposes.
const refreshInterval = 1000; // 1 second
const user_id ='01KGX14KWXN0TR47C3N36N7ZBN';

function ChatPanel({ chat_id }: { chat_id: string }) {
  // 1. SWR Hook: Fetches chat history for the given chat_id and user_id, with auto-refresh every second.
  const { data, error, isLoading } = useSWR(
    chat_id, 
    () => getChatHistory(chat_id, user_id),
    { refreshInterval: refreshInterval }
  )
  return <LoadingChatPanel />;
  if (isLoading) return <LoadingChatPanel />;
  if (error) return <div>Error loading data</div>;

  // 2. Render Messages: Maps over the fetched messages and renders a Message component for each one.
  return (
    <div className="
        flex-1 overflow-y-auto pb-4 flex flex-col-reverse  
      ">   
      {[...data].reverse().map((message: any, index: number) => (
        <Message key={index} message={message} />
      ))}
    </div>
  );
}

export default function HeadlessChatWindow({ params }: { params: Promise<{ chat_id: string }> }) {
  const { chat_id } = use(params);
  return (
    <>
      <ChatPanel chat_id={chat_id} />
      <ChatBar onSendMessage={(message) => sendMessage(chat_id, user_id, message)} />
    </>
  );
}