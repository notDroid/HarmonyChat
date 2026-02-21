import type { ChangeEvent, SyntheticEvent } from 'react';

interface ChatBarBaseProps {
  value?: string;
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void;
  onSubmit?: (e: SyntheticEvent) => void;
  loading?: boolean;
  disabled?: boolean;
}

export default function ChatBarUI({ 
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
        <div className={`flex items-center gap-2 bg-app-chatbar rounded-lg outline-1 outline-app-outline shadow-xs px-4 py-2.5 transition-opacity duration-200 ${disabled ? 'opacity-50' : ''}`}>
            <input
              type="text"
              value={value}
              onChange={onChange}
              placeholder="Type your message..." // Kept static to prevent text flashing
              disabled={disabled} // Only true hard-disable if the whole component is disabled
              className="flex-1 text-app-text outline-none bg-transparent"
            />
        </div>
      </div>
    </form>
  );
}