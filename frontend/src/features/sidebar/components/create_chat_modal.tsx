"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";

import CreateChatForm, { UserSearchResult } from "./create_chat_form";
import { getUserByEmail } from "@/features/user/api/get_user";
import { createChatAction } from "../api/create_chat_action";
import { ChatCreateRequest, ChatResponse } from "@/lib/api/model";

interface CreateChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CreateChatModalComponent({ isOpen, onClose }: CreateChatModalProps) {
  const router = useRouter();
  
  // Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // 1. Debounced Search Logic
  useEffect(() => {
    // Clear results if input is empty
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    // Set a 500ms delay before hitting the API
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        // NOTE: Currently relies on exact email match due to backend limitations
        const user = await getUserByEmail(searchQuery.trim());
        
        if (user && user.user_id) {
          setSearchResults([{
            user_id: user.user_id,
            username: user.meta?.username || user.email,
            email: user.email
          }]);
        } else {
          setSearchResults([]);
        }
      } catch (error) {
        // API throws a 404 if the user isn't found, which is expected during typing
        setSearchResults([]); 
      } finally {
        setIsSearching(false);
      }
    }, 500);

    // Cleanup function cancels the timeout if the user keeps typing
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // 2. Chat Creation Logic
  const createChatMutation = useMutation({
    mutationFn: async (payload: ChatCreateRequest) => createChatAction(payload),

    onSuccess: (newChat) => {
      // Close the modal
      onClose();
      // Redirect the user directly to their new chat room
      router.push(`/chats/${newChat?.chat_id}`);
    },
    onError: (error) => {
      console.error("Failed to create chat:", error);
      alert("Failed to create chat. Please check your connection and try again.");
    }
  });

  // 3. Handlers passed down to the Form UI
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleCreateChat = (data: { title: string; description: string; user_id_list: string[] }) => {
    // Format the payload to match the OpenAPI schema expectations
    createChatMutation.mutate({
      title: data.title || null,
      description: data.description || null,
      user_id_list: data.user_id_list,
    });
  };

  return (
    <CreateChatForm 
      isOpen={isOpen} 
      onClose={onClose}
      onSearch={handleSearch}
      onSubmit={handleCreateChat}
      searchResults={searchResults}
      isSearching={isSearching}
      isSubmitting={createChatMutation.isPending}
    />
  );
}