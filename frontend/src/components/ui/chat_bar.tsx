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
      <div className='bg-discord-bg px-2 pb-3'>
        <div className="flex items-center gap-2 bg-discord-chatbar rounded-lg outline-1 outline-discord-outline shadow-xs px-4 py-2.5">
            <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 text-discord-text outline-none "
            />
        </div>
      </div>
    </form>
  );
};