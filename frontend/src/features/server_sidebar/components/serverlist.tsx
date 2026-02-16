import Link from "next/link";
import { usePathname } from "next/navigation";
import { ServerIcon, ServerIconProps } from "../ui/icon";
import ServerSidebar from "../ui/sidebar";

export default function ServerList({ chat_id_list }: { chat_id_list: string[] }) {
  const pathname = usePathname();
  return (
    <ServerSidebar>
      {chat_id_list.map((chat_id, index) => {
        const is_active = pathname === `/chats/${chat_id}`;

        return (
          <Link key={chat_id} href={`/chats/${chat_id}`} className="w-full">
            <ServerIcon 
              server_item={({
                index,
                chat_id,
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