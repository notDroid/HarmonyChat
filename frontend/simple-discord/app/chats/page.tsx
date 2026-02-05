'use client';

import { useState, useEffect } from 'react';
import { getChatHistory, sendMessage, Message } from '@/lib/api'; // Adjust path as necessary

export default function ChatPage() {
  // --- State ---
  // We need a User ID and Chat ID to make the API calls work. 
  // In a real app, these might come from Auth context or URL params.
  const [userId, setUserId] = useState<string>(''); 
  const [chatId, setChatId] = useState<string>('');
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // --- Polling Logic ---
  useEffect(() => {
    // Don't poll if we don't have the IDs
    if (!chatId || !userId) return;

    const fetchMessages = async () => {
      try {
        const history = await getChatHistory(chatId, userId);
        setMessages(history);
        setError(null);
      } catch (err) {
        console.error(err);
        // Optional: Don't show error on UI to avoid flickering if one poll fails
      }
    };

    // 1. Fetch immediately on load/change
    fetchMessages();

    // 2. Set up polling interval (every 3 seconds)
    const intervalId = setInterval(fetchMessages, 3000);

    // 3. Cleanup on unmount or dependency change
    return () => clearInterval(intervalId);
  }, [chatId, userId]);

  // --- Handlers ---
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !chatId || !userId) return;

    try {
      await sendMessage(chatId, userId, newMessage);
      setNewMessage(''); // Clear input
      
      // Optional: Fetch immediately so the user sees their message instantly
      // instead of waiting for the next poll cycle
      const history = await getChatHistory(chatId, userId);
      setMessages(history);
    } catch (err) {
      setError('Failed to send message');
      console.error(err);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>Chat Debugger (Polling)</h1>

      {/* Configuration Section */}
      <div style={{ marginBottom: '20px', border: '1px solid #ccc', padding: '10px' }}>
        <h3>Configuration</h3>
        <div style={{ marginBottom: '5px' }}>
          <label>User ID: </label>
          <input 
            type="text" 
            value={userId} 
            onChange={(e) => setUserId(e.target.value)} 
            placeholder="Enter User UUID"
          />
        </div>
        <div>
          <label>Chat ID: </label>
          <input 
            type="text" 
            value={chatId} 
            onChange={(e) => setChatId(e.target.value)} 
            placeholder="Enter Chat UUID"
          />
        </div>
      </div>

      {/* Error Display */}
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>Error: {error}</div>}

      {/* Chat History Display */}
      <div style={{ 
        height: '300px', 
        overflowY: 'scroll', 
        border: '1px solid black', 
        padding: '10px', 
        marginBottom: '10px',
        backgroundColor: '#f9f9f9'
      }}>
        {messages.length === 0 ? (
          <p style={{ color: '#888' }}>No messages found (or waiting for IDs)...</p>
        ) : (
          messages.map((msg, index) => (
            <div key={index} style={{ marginBottom: '8px' }}>
              <strong>{msg.user_id === userId ? 'Me' : msg.user_id}:</strong> {msg.content}
              <span style={{ fontSize: '0.8em', color: '#666', marginLeft: '10px' }}>
                {msg.timestamp}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Send Message Form */}
      <form onSubmit={handleSendMessage}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
          style={{ width: '70%', padding: '5px' }}
          disabled={!chatId || !userId}
        />
        <button 
          type="submit" 
          disabled={!chatId || !userId} 
          style={{ padding: '5px 15px', marginLeft: '5px' }}
        >
          Send
        </button>
      </form>
    </div>
  );
}