import Message from "./chat_message"


export default function ChatPanel({ messages }: { messages: any[] }) {
    return (
    <div className="
        flex-1 overflow-y-auto pb-4 flex flex-col-reverse my-1
      ">   
      {[...messages].reverse().map((message: any, index: number) => (
        <Message key={index} message={message} />
      ))}
    </div>
  );
}