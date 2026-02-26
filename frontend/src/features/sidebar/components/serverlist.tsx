import Link from "next/link";
import { usePathname } from "next/navigation";
import { ServerIcon, ServerIconProps } from "../ui/icon";
import ServerSidebar from "../ui/sidebar";
import { UserChatsResponse } from "@/lib/api/model";
import CreateChat from "./create_chat"; // New simplified component

export default function ServerList({ chats }: UserChatsResponse) {
  const pathname = usePathname();

  return (
    <ServerSidebar>
      { /* New Composite Logic Component */ }
      <CreateChat />

      <div className="w-9 h-0.5 bg-app-outline rounded-full mx-auto shrink-0" />

      { /* List of User Chats */ }
      {chats.map((chat) => {
        const is_active = pathname === `/chats/${chat.chat_id}`;
        
        return (
          <Link key={chat.chat_id} href={`/chats/${chat.chat_id}`} className="w-full">
            <ServerIcon 
              server_item={({
                label: chat.meta?.title?.charAt(0).toUpperCase() || "?",
                chat_id: chat.chat_id,
                is_active,
                has_unread: false,
              }) as ServerIconProps}
            />
          </Link>
        );
      })}
    </ServerSidebar>
  );
}