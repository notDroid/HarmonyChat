import type { ChangeEvent, SyntheticEvent } from 'react';

interface ChatBarBaseProps {
  value?: string;
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void;
  onSubmit?: (e: SyntheticEvent) => void;
  loading?: boolean;
  disabled?: boolean;
}

export default function ChatBarVisual({ 
  value = "", 
  onChange, 
  onSubmit, 
  loading = false,
  disabled = false
}: ChatBarBaseProps) {
  return (
    <form 
      onSubmit={onSubmit} 
      className="w-full"
    >
      <div className='bg-app-bg px-2 pb-3'>
        <div className={`flex items-center gap-2 bg-app-chatbar rounded-lg outline-1 outline-app-outline shadow-xs px-4 py-2.5 ${loading || disabled ? 'opacity-50' : ''}`}>
            <input
              type="text"
              value={value}
              onChange={onChange}
              placeholder={loading ? "Sending..." : "Type your message..."}
              disabled={loading || disabled}
              className="flex-1 text-app-text outline-none bg-transparent"
            />
        </div>
      </div>
    </form>
  );
}
