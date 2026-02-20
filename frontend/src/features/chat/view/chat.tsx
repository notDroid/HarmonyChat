// Views
import ChatHeaderView from "./header";
import ChatPanelView from "../components/panel";
import ChatBarView from "../components/bar";

// UI Components
import ErrorChatPanel from "../ui/error";

// API Functions
import getChatHistory from "../api/get_chat_history";
import { ApiError, NetworkError } from "@/lib/utils/errors";
import { isNextRedirect } from "@/lib/utils/utils";

// React Query
import { QueryClient, dehydrate, HydrationBoundary } from '@tanstack/react-query';

export default async function ChatWindowView({ chat_id }: { chat_id: string }) {
  // Initialize a request-scoped QueryClient for the Server Component
  const queryClient = new QueryClient();

  try {
    // Attempt to prefetch the chat history on the server and populate the QueryClient cache
    await queryClient.fetchQuery({
      queryKey: ['chatHistory', chat_id],
      queryFn: () => getChatHistory(chat_id),
    });
  
  } catch (error) {
    if (isNextRedirect(error)) throw error; 

    console.log("Failed to fetch initial chat history:", error);
    
    // Throw the error page on API errors
    if (error instanceof ApiError) {
      return <ErrorChatPanel message={`${error.message}`} />;
    } 
    // Fallback to loading/empty state for network errors, throw otherwise
    else if (!(error instanceof NetworkError)) {
      throw error;
    }
  }

  return (
    <div className="flex h-full w-full flex-col min-w-0">
      <ChatHeaderView />
        <HydrationBoundary state={dehydrate(queryClient)}>
            <ChatPanelView chat_id={chat_id} />
        </HydrationBoundary>
      <ChatBarView chat_id={chat_id} />
    </div>
  );
}