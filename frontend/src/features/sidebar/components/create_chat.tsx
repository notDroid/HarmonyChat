"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useDebounce } from "use-debounce";

import { createChatAction } from "../api/create_chat_action";
import { useSidebarCache } from "../api/cache";
import { createChatSchema, CreateChatFormValues } from "../utils/validation";
import { CreateChatDialog, CreateChatTrigger, CreateChatContent } from "../ui/create_chat";
import { ApiError } from "@/lib/utils/errors";

import { useUserSearch } from "@/features/user/api/use_user_search";

export type UserSearchResult = {
  user_id: string;
  username: string;
  email: string;
};

export default function CreateChat() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [rootError, setRootError] = useState<string | null>(null);
  
  const { addChat } = useSidebarCache();
  
  const form = useForm<CreateChatFormValues>({
    resolver: zodResolver(createChatSchema),
    defaultValues: {
      title: "",
      description: "",
      search: "",
      user_id_list: [],
    },
  });

  const searchValue = useWatch({ control: form.control, name: "search" });
  const [debouncedSearch] = useDebounce(searchValue || "", 500);
  
  // 2. Let React Query manage the fetching, caching, and loading state
  const { data: users, isFetching: isSearching } = useUserSearch(debouncedSearch);
  
  const [selectedUsersDisplay, setSelectedUsersDisplay] = useState<UserSearchResult[]>([]);

  // 3. Transform the raw API data into your UI format on the fly
  const searchResults: UserSearchResult[] = (users || []).map(user => ({
    user_id: user.user_id,
    username: user.meta?.username || user.email,
    email: user.email
  }));

  const handleAddUser = (user: UserSearchResult) => {
    const currentIds = form.getValues("user_id_list") || [];
    if (currentIds.includes(user.user_id)) return;
    
    form.setValue("user_id_list", [...currentIds, user.user_id], { shouldValidate: true });
    setSelectedUsersDisplay(prev => [...prev, user]);
    
    // Clearing the search field causes `debouncedSearch` to empty out,
    // automatically disabling the query and hiding the results.
    form.setValue("search", "");
  };

  const handleRemoveUser = (id: string) => {
    const currentIds = form.getValues("user_id_list") || [];
    form.setValue("user_id_list", currentIds.filter(uid => uid !== id), { shouldValidate: true });
    setSelectedUsersDisplay(prev => prev.filter(u => u.user_id !== id));
  };

  const mutation = useMutation({
    mutationFn: (data: CreateChatFormValues) => createChatAction({
      title: data.title,
      description: data.description || null,
      user_id_list: data.user_id_list
    }),
    onSuccess: (newChat) => {
      addChat(newChat);
      
      setOpen(false);
      form.reset();
      setSelectedUsersDisplay([]);
      setRootError(null);

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
        searchValue={searchValue || ""}
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