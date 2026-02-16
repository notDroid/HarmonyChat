import { use } from 'react';
import ChatWindowView from "@/features/chat/view/chat";


export default function ChatWindow({ params }: { params: Promise<{ chat_id: string }> }) {
  const { chat_id } = use(params);
  return <ChatWindowView chat_id={chat_id} />;
}