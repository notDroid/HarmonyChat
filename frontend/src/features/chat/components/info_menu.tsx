"use client";

import { useState } from "react";
import { useDeleteChat } from "../api/use_delete_chat";
import { ChatInfoDialog, ChatInfoTrigger, ChatInfoContent } from "../ui/info_dialog";

export default function ChatInfoMenu({ chat_id }: { chat_id: string }) {
  const [open, setOpen] = useState(false);
  const { mutate: deleteChat, isPending } = useDeleteChat();

  const handleDelete = () => {
    if (confirm("Are you sure you want to permanently delete this chat?")) {
      deleteChat(chat_id, {
        onSuccess: () => setOpen(false)
      });
    }
  };

  return (
    <ChatInfoDialog open={open} onOpenChange={setOpen}>
      <ChatInfoTrigger />
      <ChatInfoContent 
        onDelete={handleDelete} 
        isDeleting={isPending} 
      />
    </ChatInfoDialog>
  );
}