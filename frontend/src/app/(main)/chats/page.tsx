import { redirect } from "next/navigation";
// import { getChatList } from "@/lib/api";


export default async function HomePage() {
  // For now return a blank page. We can implement the actual chat list later. The main point of this page is just to redirect to the first chat.
  return (
    <div className="flex items-center justify-center h-screen">
      <h1 className="text-2xl font-bold">Welcome to Simple Discord!</h1>
    </div>
  );
  // const data = await getChatList(user_id);
  // const chat_ids = data.chat_id_list;

  // if (!chat_ids || chat_ids.length === 0) {
  //   return <div>No chats</div>;
  // }

  // redirect(`/chats/${chat_ids[0]}`);
}