export default function Message({message}: { message: any; }) {
    const date = new Date(message.timestamp).toLocaleString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true
    });
  
    return (
    <div className="px-3 py-4 text-sm">
      <strong className="mr-1 text-white">
        {message.user_id}
      </strong>
      <span className="text-xs text-white">
        {date}
      </span>
      <div className="mt-1 text-white">
        {message.content}
      </div>
    </div>
  );
}