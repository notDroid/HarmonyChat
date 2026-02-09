import { redirect } from "next/navigation";
import { getChatList } from "@/lib/api";

// Temporary constant for demo purposes.
const user_id = '01KGX14KWXN0TR47C3N36N7ZBN'; 

export default async function HomePage() {
  const data = await getChatList(user_id);
  const chat_ids = data.chat_id_list;

  if (!chat_ids || chat_ids.length === 0) {
    return <div>No chats</div>;
  }

  redirect(`/chats/${chat_ids[0]}`);
}