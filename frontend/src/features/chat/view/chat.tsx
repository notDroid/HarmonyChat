import { Suspense } from "react";

// Views
import ChatHeaderComponent from "../components/header";
import ChatPanel from "../components/panel";

// UI Components
import ChatBar from "../components/bar";
import { NetworkError } from "@/lib/utils/errors";
import LoadingChatPanel from "../ui/loading";

// React Query
import { QueryClient, dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { prefetchChatHistory } from "../api/cache";

// Try to prefetch the chat history on the server to populate the cache before rendering the ChatPanel
async function PrefetchedChatPanel({ chat_id }: { chat_id: string }) {
  const queryClient = new QueryClient();

  try {
    await prefetchChatHistory(queryClient, chat_id);
  } catch (error) {    
    if (!(error instanceof NetworkError)) {
      throw error;
    }
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ChatPanel chat_id={chat_id} />
    </HydrationBoundary>
  );
}

export default function ChatWindowView({ chat_id }: { chat_id: string }) {
  return (
    <div className="flex h-full w-full flex-col min-w-0">
      <ChatHeaderComponent chat_id={chat_id} />
      
      {/* Wait for the server to get this component only, everything else can be loaded on the client side immediately */ }
      <Suspense fallback={<LoadingChatPanel />}>
        <PrefetchedChatPanel chat_id={chat_id} />
      </Suspense>
      
      <ChatBar chat_id={chat_id} />
    </div>
  );
}