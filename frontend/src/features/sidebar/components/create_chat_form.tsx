"use client";

import { useState, SyntheticEvent, useEffect } from "react";
import CreateChatModalUI from "../ui/create_chat_modal";

export type UserSearchResult = {
  user_id: string;
  username: string;
  email: string;
};

interface CreateChatFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string; description: string; user_id_list: string[] }) => void;
  onSearch: (query: string) => void;
  searchResults: UserSearchResult[];
  isSearching: boolean;
  isSubmitting: boolean;
}

export default function CreateChatForm({
  isOpen,
  onClose,
  onSubmit,
  onSearch,
  searchResults,
  isSearching,
  isSubmitting
}: CreateChatFormProps) {
  // Form State
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [selectedUsers, setSelectedUsers] = useState<UserSearchResult[]>([]);

  // Trigger search application logic when input changes
  useEffect(() => {
    onSearch(searchInput);
  }, [searchInput, onSearch]);

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setTitle("");
      setDescription("");
      setSearchInput("");
      setSelectedUsers([]);
    }
  }, [isOpen]);

  const handleAddUser = (user: UserSearchResult) => {
    if (selectedUsers.length >= 10) return;
    if (selectedUsers.some(u => u.user_id === user.user_id)) return;

    setSelectedUsers([...selectedUsers, user]);
    setSearchInput(""); // Clear search bar after selection
  };

  const handleRemoveUser = (userId: string) => {
    setSelectedUsers(selectedUsers.filter(u => u.user_id !== userId));
  };

  const handleSubmit = (e: SyntheticEvent) => {
    e.preventDefault();
    
    if (selectedUsers.length === 0) return;

    onSubmit({
      title: title.trim(),
      description: description.trim(),
      user_id_list: selectedUsers.map(u => u.user_id)
    });
  };

  return (
    <CreateChatModalUI 
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      setTitle={setTitle}
      description={description}
      setDescription={setDescription}
      searchInput={searchInput}
      setSearchInput={setSearchInput}
      selectedUsers={selectedUsers}
      onAddUser={handleAddUser}
      onRemoveUser={handleRemoveUser}
      onSubmit={handleSubmit}
      searchResults={searchResults}
      isSearching={isSearching}
      isSubmitting={isSubmitting}
      isValid={selectedUsers.length > 0 && selectedUsers.length <= 10}
    />
  );
}