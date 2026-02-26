// Views
import ChatHeader from "../ui/header";
import ChatPanel from "../components/panel";

// UI Components
import ErrorChatPanel from "../ui/error";
import ChatBar from "../components/bar";

// API Functions
import { ApiError, NetworkError, isNextRedirect } from "@/lib/utils/errors";

// React Query
import { QueryClient, dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { prefetchChatHistory } from "../api/cache";

export default async function ChatWindowView({ chat_id }: { chat_id: string }) {
  const queryClient = new QueryClient();

  try {
    await prefetchChatHistory(queryClient, chat_id);
  } catch (error) {
    if (isNextRedirect(error)) throw error; 
    
    if (error instanceof NetworkError) {
      // Gracefully fail and let client render page
    }
    else if (error instanceof ApiError) {
      return <ErrorChatPanel message={`${error.message}`} />;
    } 
    else {
      return <ErrorChatPanel message={'Unable to load chat. Please try again later.'} />;
    }
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