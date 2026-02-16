import LoadingChatPanel from "../ui/loading"
import ChatBar from "../ui/bar"
import ChatHeaderView from "./header";

export default async function LoadingChatWindowView() {
  return (
    <div className="flex h-full w-full flex-col min-w-0">    
        <ChatHeaderView />  
        <LoadingChatPanel />
        <ChatBar />
    </div>
  );
}