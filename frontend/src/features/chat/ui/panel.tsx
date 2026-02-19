import { ChatMessage } from "@/lib/api/model/chatMessage";
import Message from "./message"


export default function ChatPanel({ messages }: { messages: ChatMessage[] }) {
    return (
    <div className="
        flex-1 overflow-y-auto pb-4 flex flex-col-reverse my-1
      ">   
      {[...messages].reverse().map((message: any, index: number) => (
        <Message key={message.ulid} message={message} />
      ))}
    </div>
  );
}