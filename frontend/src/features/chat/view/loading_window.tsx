import LoadingChatPanel from "../ui/chat_loading_panel"
import ChatBar from "../ui/chat_bar"
import ChatHeaderView from "./chat_header";

export default async function LoadingChatWindowView() {
  return (
    <div className="flex h-full w-full flex-col min-w-0">    
        <ChatHeaderView />  
        <LoadingChatPanel />
        <ChatBar />
    </div>
  );
}