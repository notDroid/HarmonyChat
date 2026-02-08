"use client";
import { useState } from 'react';


export default function ChatBar({ onSendMessage }: { onSendMessage: (message: string) => void }) {
  const [message, setMessage] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSendMessage(message);
    setMessage('');
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      className="w-full"
    >
      <div className="flex items-center gap-2 bg-discord-chatbar rounded-lg px-4 py-2.5">
          <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 text-discord-text outline-none "
          />
          
          <button
          type="submit"
          disabled={!message.trim()}
          className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Send message"
          >
          Send
          </button>
      </div>
    </form>
  );
};