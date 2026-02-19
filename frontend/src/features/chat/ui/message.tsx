import { ChatMessage } from "@/lib/api/model/chatMessage";

const defaultIcon = "/assets/avatars/0.png";

export default function Message({ message }: { message: ChatMessage }) {
  const date = new Date(message.timestamp).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  return (
    <div className="
    grid grid-cols-[auto_minmax(0,1fr)] 
    gap-3 w-full px-3 py-4
    text-sm hover:bg-app-hover transition-colors
    ">
      
      {/* Icon */}
      <div className="cursor-pointer mt-0.5">
        <img 
            // 2. The Logic: Use the avatar_url OR (||) the defaultIcon
            src={defaultIcon} // Replace with message.avatar_url || defaultIcon after adding icons ---------------------------------------- TODO
            
            // Accessibility: Always include descriptive alt text
            alt={`${message.user_id}'s avatar`}
            
            // Styling: Fixed width/height, circle shape, cover fit
            className="w-10 h-10 rounded-full object-cover"
        />
      </div>

      <div className="flex flex-col">
        {/* User name and timestamp */}
        <div className="flex items-baseline gap-2 break-all">
          <span className="cursor-pointer font-medium text-app-text hover:underline">
            {message.user_id}
          </span>
          <span className="font-light text-xs text-app-muted cursor-default select-none break-all">
            {date}
          </span>
        </div>

        {/* Message content */}
        <div className="text-app-text leading-5.5 wrap-break-word whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    </div>
  );
}