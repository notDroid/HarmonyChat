import LoadingChatPanel from "../ui/loading"
import ChatBar from "../ui/bar"
import ChatHeader from "../ui/header";

export default async function LoadingChatWindowView() {
  return (
    <div className="flex h-full w-full flex-col min-w-0">    
        <ChatHeader />  
        <LoadingChatPanel />
        <ChatBar disabled />
    </div>
  );
}