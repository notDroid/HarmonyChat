import LoadingChatPanel from "./loading"
import ChatBar from "./bar"
import ChatHeaderSkeleton from "./loading_header";

export default async function LoadingChatWindowView() {
  return (
    <div className="flex h-full w-full flex-col min-w-0">    
        <ChatHeaderSkeleton />  
        <LoadingChatPanel />
        <ChatBar disabled />
    </div>
  );
}