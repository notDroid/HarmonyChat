"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useDebounce } from "use-debounce";

import { createChatAction } from "../api/create_chat_action";
import { getUserByEmail } from "@/features/user/api/get_user";
import { useSidebarCache } from "../api/cache"; // Import the cache hook
import { createChatSchema, CreateChatFormValues } from "../utils/validation";
import { CreateChatDialog, CreateChatTrigger, CreateChatContent } from "../ui/create_chat";
import { ApiError } from "@/lib/utils/errors";

export type UserSearchResult = {
  user_id: string;
  username: string;
  email: string;
};

export default function CreateChat() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [rootError, setRootError] = useState<string | null>(null);
  
  // Access the cache utility
  const { addChat } = useSidebarCache();
  
  // 1. Form Management
  const form = useForm<CreateChatFormValues>({
    resolver: zodResolver(createChatSchema),
    defaultValues: {
      title: "",
      description: "",
      search: "",
      user_id_list: [],
    },
  });

  // 2. Search Logic
  const searchValue = useWatch({ control: form.control, name: "search" });
  const [debouncedSearch] = useDebounce(searchValue, 500);
  
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  const [selectedUsersDisplay, setSelectedUsersDisplay] = useState<UserSearchResult[]>([]);

  useEffect(() => {
    if (!debouncedSearch || debouncedSearch.trim() === "") {
      setSearchResults([]);
      return;
    }
    
    const fetchUser = async () => {
      setIsSearching(true);
      try {
        const user = await getUserByEmail(debouncedSearch.trim());
        if (user) {
          setSearchResults([{
            user_id: user.user_id,
            username: user.meta?.username || user.email,
            email: user.email
          }]);
        } else {
            setSearchResults([]);
        }
      } catch (e) {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    fetchUser();
  }, [debouncedSearch]);

  const handleAddUser = (user: UserSearchResult) => {
    const currentIds = form.getValues("user_id_list") || [];
    if (currentIds.includes(user.user_id)) return;
    
    form.setValue("user_id_list", [...currentIds, user.user_id], { shouldValidate: true });
    setSelectedUsersDisplay(prev => [...prev, user]);
    
    form.setValue("search", "");
    setSearchResults([]);
  };

  const handleRemoveUser = (id: string) => {
    const currentIds = form.getValues("user_id_list") || [];
    form.setValue("user_id_list", currentIds.filter(uid => uid !== id), { shouldValidate: true });
    setSelectedUsersDisplay(prev => prev.filter(u => u.user_id !== id));
  };

  // 4. API Mutation
  const mutation = useMutation({
    mutationFn: (data: CreateChatFormValues) => createChatAction({
      title: data.title,
      description: data.description || null,
      user_id_list: data.user_id_list
    }),
    onSuccess: (newChat) => {
      // 1. Update the sidebar cache immediately
      addChat(newChat);

      // 2. Close and Reset
      setOpen(false);
      form.reset();
      setSelectedUsersDisplay([]);
      setSearchResults([]);
      setRootError(null);

      // 3. Navigate
      router.push(`/chats/${newChat.chat_id}`);
    },
    onError: (error) => {
      let msg = "Failed to create chat.";
      if (error instanceof ApiError) {
        msg = error.message;
      } else if (error instanceof Error) {
        msg = error.message;
      }
      setRootError(msg);
    }
  });

  const onSubmit = (data: CreateChatFormValues) => {
    setRootError(null);
    mutation.mutate(data);
  };

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) {
      form.reset();
      setSelectedUsersDisplay([]);
      setSearchResults([]);
      setRootError(null);
    }
  };

  return (
    <CreateChatDialog open={open} onOpenChange={handleOpenChange}>
      <CreateChatTrigger />
      <CreateChatContent 
        form={form}
        onSubmit={onSubmit}
        isSubmitting={mutation.isPending}
        searchValue={searchValue!}
        searchResults={searchResults}
        isSearching={isSearching}
        onAddUser={handleAddUser}
        onRemoveUser={handleRemoveUser}
        selectedUsers={selectedUsersDisplay}
        rootError={rootError}
      />
    </CreateChatDialog>
  );
}