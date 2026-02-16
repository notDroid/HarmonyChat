// Views
import ChatHeaderView from "./header";
import ChatPanelView from "../components/panel";
import ChatBarView from "../components/bar";

// UI Components
import ErrorChatPanel from "../ui/error";

// API Functions
import getChatHistory from "../api/get_chat_history";
import { ChatMessage } from "@/lib/api/model";
import { ApiError, NetworkError } from "@/lib/utils/errors";
import { isNextRedirect } from "@/lib/utils/utils";

const refreshInterval = 1000;

export default async function ChatWindowView({ chat_id }: { chat_id: string }) {
  let initial_messages: ChatMessage[] = [];
  let loaded = false;

  try {
    // await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate loading delay
    initial_messages = await getChatHistory(chat_id);
    loaded = true;
  
  } catch (error) {
    if (isNextRedirect(error)) throw error; 

    console.log("Failed to fetch initial chat history:", error);
    // Throw the error page on API errors, for network errors fall back to the loading page.
    if (error instanceof ApiError) {
      return <ErrorChatPanel message={`${error.message}`} />;
    } else if (!(error instanceof NetworkError)) {
      throw error;
    }

  }

  return (
    <div className="flex h-full w-full flex-col min-w-0">
      <ChatHeaderView />
      <ChatPanelView chat_id={chat_id} refreshInterval={refreshInterval} initial_messages={initial_messages} loaded={loaded} />
      <ChatBarView chat_id={chat_id} />
    </div>
  );
}