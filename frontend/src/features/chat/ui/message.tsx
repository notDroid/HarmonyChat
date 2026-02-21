import { ChatMessage } from "@/lib/api/model/chatMessage";

export interface UIMessage extends ChatMessage {
  tempId?: string; 
  status?: 'pending' | 'error' | 'sent'; 
}

const defaultIcon = "/assets/avatars/0.png";

export function Message(
  { message, onRetry }: 
  { message: UIMessage, onRetry?: (msg: UIMessage) => void }
) {
  const date = new Date(message.timestamp).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  const isPending = message.status === 'pending';
  const isError = message.status === 'error';

  return (
    <div className="
      grid grid-cols-[auto_minmax(0,1fr)] 
      gap-3 w-full px-3 py-3.5 mt-1
      text-sm hover:bg-app-hover transition-colors
    ">
      
      {/* Icon */}
      <div className={`cursor-pointer mt-0.5 shrink-0 transition-opacity duration-300 ${isPending ? 'opacity-70' : ''}`}>
        <img 
            src={defaultIcon} 
            alt={`${message.user_id}'s avatar`}
            className="w-10 h-10 rounded-full object-cover"
        />
      </div>

      <div className="flex flex-col min-w-0">
        {/* User name and timestamp */}
        <div className={`flex items-baseline gap-2 truncate transition-opacity duration-300 ${isPending ? 'opacity-70' : ''}`}>
          <span className="cursor-pointer font-medium text-app-text hover:underline truncate">
            {message.user_id}
          </span>
          <span className="font-light text-xs text-app-muted cursor-default select-none shrink-0">
            {date}
          </span>
        </div>

        {/* Message Content Container */}
        <div className="leading-5.5 wrap-break-word whitespace-pre-wrap mt-0.5">
          
          {/* Message Text - Pulses and turns gray when pending */}
          <div className={`transition-all duration-300 ${
            isPending 
              ? 'text-app-muted animate-pulse' 
              : 'text-app-text'
          }`}>
            {message.content}
          </div>
          
          {/* Error State */}
          {isError && (
            <div className="mt-2 text-xs text-[var(--color-red)] flex items-center gap-1.5 font-medium">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2.5" 
                strokeLinecap="round" 
                strokeLinejoin="round"
                className="w-3.5 h-3.5"
              >
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>Failed to send.</span>
              <button 
                onClick={() => onRetry && onRetry(message)}
                className="font-bold hover:underline hover:text-app-text transition-colors cursor-pointer ml-1"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}