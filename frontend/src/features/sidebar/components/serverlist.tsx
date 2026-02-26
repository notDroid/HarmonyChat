import Link from "next/link";
import { usePathname } from "next/navigation";
import { ServerIcon, ServerIconProps } from "../ui/icon";
import ServerSidebar from "../ui/sidebar";

import { UserChatsResponse } from "@/lib/api/model";
import CreateChatButtonComponent from "./create_button";
import CreateChatModalComponent from "./create_chat_modal";

import { useState } from "react";

export default function ServerList({ chats }: UserChatsResponse) {
  const pathname = usePathname();

  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <ServerSidebar>
      { /* Create Chat Button at the top of the sidebar */ }
      <CreateChatButtonComponent onClick={() => setIsModalOpen(true)} />

      { /* List of User Chats */ }
      {chats.map((chat) => {
        const is_active = pathname === `/chats/${chat.chat_id}`;
        
        const title = chat.meta?.title || "?";
        const label = title.charAt(0).toUpperCase();

        return (
          <Link key={chat.chat_id} href={`/chats/${chat.chat_id}`} className="w-full">
            <ServerIcon 
              server_item={({
                label,
                chat_id: chat.chat_id,
                is_active,
                has_unread: false,
              }) as ServerIconProps}
            />
          </Link>
        );
      })}

      { /* Create Chat Modal Component */ }
      <CreateChatModalComponent 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />
    </ServerSidebar>
  );
}