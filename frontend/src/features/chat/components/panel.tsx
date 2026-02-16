// 'use client';

// import useSWR from 'swr';

// import { getChatHistory} from "@/lib/api";

// import ChatPanel from "../ui/chat_panel";
// import LoadingChatPanel from "../ui/chat_loading_panel"


// export default function ChatPanelView(
//   { chat_id, user_id, refreshInterval, initial_messages = [], loaded = false }: 
//   { chat_id: string, user_id: string, refreshInterval: number, initial_messages: any[], loaded: boolean }
// ) {
//   // SWR Hook: Fetches chat history for the given chat_id and user_id.
//   const { data, isLoading } = useSWR(
//     chat_id, 
//     () => getChatHistory(chat_id, user_id),
//     { refreshInterval: refreshInterval, fallbackData: initial_messages }
//   )

//   if (isLoading && !loaded) {
//     return <LoadingChatPanel />;
//   }

//   return <ChatPanel messages={data.messages} />;
// }