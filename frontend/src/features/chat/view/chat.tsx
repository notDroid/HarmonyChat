// Views
import ChatHeader from "../ui/header";
import ChatPanel from "../components/panel";

// UI Components
import ChatBar from "../components/bar";

// API Functions
import { NetworkError } from "@/lib/utils/errors";

// React Query
import { QueryClient, dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { prefetchChatHistory } from "../api/cache";

export default async function ChatWindowView({ chat_id }: { chat_id: string }) {
  const queryClient = new QueryClient();

  try {
    await prefetchChatHistory(queryClient, chat_id);
  } catch (error) {    
    if (!(error instanceof NetworkError)) {
      throw error;
    }
    // Gracefuly fail to load on network error and let client handle it
  }

  return (
    <div className="flex h-full w-full flex-col min-w-0">
      <ChatHeader />
        <HydrationBoundary state={dehydrate(queryClient)}>
            <ChatPanel chat_id={chat_id} />
        </HydrationBoundary>
      <ChatBar chat_id={chat_id} />
    </div>
  );
}