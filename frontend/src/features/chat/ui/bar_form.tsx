"use client";

import { useState, type SyntheticEvent } from 'react';
import ChatBarVisual from './bar';

interface ChatBarProps {
  onSendMessage: (message: string) => void;
  loading?: boolean;
}

export default function ChatBar({ onSendMessage, loading = false }: ChatBarProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: SyntheticEvent) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    onSendMessage(message);
    setMessage("");
  };

  return (
    <ChatBarVisual 
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onSubmit={handleSubmit}
        loading={loading}
    />
  );
};