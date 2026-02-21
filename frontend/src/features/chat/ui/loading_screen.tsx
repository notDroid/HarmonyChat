import LoadingChatPanel from "./loading"
import ChatBar from "./bar"
import ChatHeader from "./header";

export default async function LoadingChatWindowView() {
  return (
    <div className="flex h-full w-full flex-col min-w-0">    
        <ChatHeader />  
        <LoadingChatPanel />
        <ChatBar disabled />
    </div>
  );
}