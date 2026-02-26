import Link from "next/link";
import { usePathname } from "next/navigation";
import { ServerIcon, ServerIconProps } from "../ui/icon";
import ServerSidebar from "../ui/sidebar";

import { UserChatsResponse } from "@/lib/api/model";

export default function ServerList({ chats }: UserChatsResponse) {
  const pathname = usePathname();

  return (
    <ServerSidebar>
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
    </ServerSidebar>
  );
}