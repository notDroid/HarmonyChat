import { UIMessage, Message } from "./message";
import LoadingChatPanel from "./loading";
import { RefCallback } from "react";

interface ChatPanelProps {
  messages: UIMessage[];
  observerTarget?: RefCallback<Element>;
  isFetchingNextPage?: boolean;
  onRetry?: (msg: UIMessage) => void;
}

export default function ChatPanel({ messages, observerTarget, isFetchingNextPage, onRetry }: ChatPanelProps) {
  return (
    <div className="flex-1 overflow-y-auto pb-4 flex flex-col-reverse my-1">   
      {[...messages].reverse().map((message: UIMessage) => (
        <Message key={message.ulid} message={message} onRetry={onRetry} />
      ))}
      
      Invisible anchor at the "top" of the scroll container to trigger pagination
      <div ref={observerTarget} className="mb-[-1]">
        {isFetchingNextPage && <LoadingChatPanel repeatCount={2} />}
      </div>
    </div>
  );
}