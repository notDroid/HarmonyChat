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
import { CHAT_PANEL_SETTINGS } from '@/settings/chat_panel';

export default async function ChatWindowView({ chat_id }: { chat_id: string }) {
  const queryClient = new QueryClient();

  try {
    // 1. Swap fetchQuery for prefetchInfiniteQuery
    await queryClient.prefetchInfiniteQuery({
      queryKey: [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id],
      queryFn: () => getChatHistory(chat_id, 50), // Pass the initial limit
      initialPageParam: undefined as string | undefined,
    });
  } catch (error) {
    if (isNextRedirect(error)) throw error; 

    console.log("Failed to fetch initial chat history:", error);

    if (error instanceof ApiError) {
      return <ErrorChatPanel message={`${error.message}`} />;
    } 
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