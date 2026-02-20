import { ChatMessage } from "@/lib/api/model/chatMessage";
import Message from "./message"
import LoadingChatPanel from "./loading";
import { RefCallback } from "react";

interface ChatPanelProps {
  messages: ChatMessage[];
  observerTarget?: RefCallback<Element>;
  isFetchingNextPage?: boolean;
}

export default function ChatPanel({ messages, observerTarget, isFetchingNextPage }: ChatPanelProps) {
  return (
    <div className="flex-1 overflow-y-auto pb-4 flex flex-col-reverse my-1">   
      {[...messages].reverse().map((message: ChatMessage) => (
        <Message key={message.ulid} message={message} />
      ))}
      
      {/* Invisible anchor at the "top" of the scroll container to trigger pagination */}
      <div ref={observerTarget} className="mb-[-1]">
        {isFetchingNextPage && <LoadingChatPanel repeatCount={2} />}
      </div>
    </div>
  );
}