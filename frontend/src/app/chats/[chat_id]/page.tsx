'use client';

import { use, useState, useEffect } from 'react';
import useSWR from 'swr';
import Message from "@/components/ui/message"

const host_name = "macbook-pro";
const API_ENDPOINT = `http://${host_name}:8000/api/v1/`;
const user_id ='01KGWSCDW9J1NEY5ZV4WFA4YMH';
const refreshInterval = 1000; // 1 second

async function getChatHistory(chat_id: string, user_id: string) {
  const res = await fetch(`${API_ENDPOINT}chats/${chat_id}?user_id=${user_id}`);
  if (!res.ok) {
    throw new Error('Failed to fetch chat history');
  }
  const data = await res.json();
  return data.messages;
}

async function sendMessage(chat_id: string, user_id: string, content: string) {
  const res = await fetch(`${API_ENDPOINT}chats/${chat_id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id, content }),
  });
  if (!res.ok) {
    throw new Error('Failed to send message');
  }
  const data = await res.json();
  return data;
}



export function ChatBar({ onSendMessage }: { onSendMessage: (message: string) => void }) {
  const [message, setMessage] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSendMessage(message);
    setMessage('');
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <form 
        onSubmit={handleSubmit} 
        className="flex items-center gap-2 border rounded-full px-4 py-2 shadow-sm bg-white focus-within:ring-2 ring-blue-500"
      >
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 text-black bg-transparent outline-none py-2"
        />
        
        <button
          type="submit"
          disabled={!message.trim()}
          className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Send message"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default function ChatPage({ params }: { params: Promise<{ chat_id: string }> }) {
  const { chat_id } = use(params);
  const endpoint = `${API_ENDPOINT}chats/${chat_id}?user_id=${user_id}`;
  const { data, error, isLoading } = useSWR(
    endpoint, 
    () => getChatHistory(chat_id, user_id),
    { refreshInterval: refreshInterval }
  )

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading data</div>;

  return (
    <div>
      {data.map((message: any, index: number) => (
        <Message key={index} message={message} />
      ))}
      <ChatBar onSendMessage={(message) => sendMessage(chat_id, user_id, message)} />
    </div>
  );
}