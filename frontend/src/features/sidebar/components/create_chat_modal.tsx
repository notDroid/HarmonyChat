"use client";

import { useState } from "react";
import CreateChatForm, { UserSearchResult } from "./create_chat_form";

interface CreateChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CreateChatModalComponent({ isOpen, onClose }: CreateChatModalProps) {
  // TODO: Implement use_user_search hook (with debouncing)
  const [mockSearchResults, setMockSearchResults] = useState<UserSearchResult[]>([]);
  const isSearching = false; 

  // TODO: Implement use_create_chat hook
  const isSubmitting = false;

  const handleSearch = (query: string) => {
    // TODO: Pass query to your debounced search hook
    console.log("Searching for:", query);
  };

  const handleCreateChat = (data: { title: string; description: string; user_id_list: string[] }) => {
    // TODO: Call your mutation here
    // onSuccess: invalidate sidebar cache, close modal, and redirect to new chat
    console.log("Creating chat with payload:", data);
  };

  return (
    <CreateChatForm 
      isOpen={isOpen} 
      onClose={onClose}
      onSearch={handleSearch}
      onSubmit={handleCreateChat}
      searchResults={mockSearchResults}
      isSearching={isSearching}
      isSubmitting={isSubmitting}
    />
  );
}