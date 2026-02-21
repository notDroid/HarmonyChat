"use client";

import { useState, type SyntheticEvent } from 'react';
import ChatBarUI from '../ui/bar';

interface ChatBarProps {
  onSendMessage: (message: string) => void;
  loading?: boolean;
}

export default function ChatBarForm({ onSendMessage, loading = false }: ChatBarProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: SyntheticEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    onSendMessage(message);
    setMessage("");
  };

  return (
    <ChatBarUI 
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onSubmit={handleSubmit}
        loading={loading}
    />
  );
};