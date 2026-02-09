export interface ServerIconProps {
  index: number;
  chat_id: string;
  icon_url?: string;
  has_unread: boolean;
  is_active: boolean;
}

export function ServerIcon(
  { server_item }: { server_item: ServerIconProps }
) {

  return (
    <div className="relative group flex items-center justify-center w-full my-1">
      <div 
        className={`
          absolute left-0 
          bg-app-text 
          rounded-r-full 
          w-pill
          transition-all duration-200 ease-in-out
          -translate-x-0.5
          
          ${server_item.is_active 
            ? 'h-pill-active' 
            : server_item.has_unread 
              ? 'h-pill-small group-hover:h-pill-hover'
              : 'h-0          group-hover:h-pill-hover'
          }
        `}
      />

      <button className={`
          h-server-icon w-server-icon
          flex items-center justify-center
          transition-all duration-200 ease-linear
          shadow-sm
          overflow-hidden  /* Added: Ensures the image clips to the circle/rounded shape */
          
          ${server_item.is_active ? 'rounded-server-icon-expanded' : 'rounded-[50%] group-hover:rounded-server-icon-expanded'}

          ${server_item.is_active 
            ? 'bg-brand text-white' 
            : 'bg-app-sidebar text-app-text group-hover:bg-brand group-hover:text-white'
          }
      `}>
        {/* Render Image if URL exists, otherwise render ID */}
        {server_item.icon_url ? (
          <img 
            src={server_item.icon_url} 
            alt={`Server ${server_item.chat_id} Icon`}
            className="w-full h-full object-cover" 
          />
        ) : (
          server_item.index
        )}
      </button>
    </div>
  );
}