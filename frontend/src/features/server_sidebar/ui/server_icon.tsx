
export default function ServerIcon(
  { label, active, unread }: 
  { label: string; active?: boolean; unread?: boolean }
) {
  return (
    <div className="relative group flex items-center justify-center w-full my-1">
      <div 
        className={`
          absolute left-0 
          bg-discord-text 
          rounded-r-full 
          w-pill
          transition-all duration-200 ease-in-out
          -translate-x-0.5 /* Slight pull back to hide fully when h-0 */
          
          ${active 
            ? 'h-pill-active'                           // Top Priority: Active
            : unread 
              ? 'h-pill-small group-hover:h-pill-hover' // Unread logic (Small -> Grow on hover)
              : 'h-0          group-hover:h-pill-hover' // Normal logic (Hidden -> Grow on hover)
          }
        `}
      />

      <button className={`
          h-server-icon w-server-icon
          flex items-center justify-center
          transition-all duration-200 ease-linear
          shadow-sm
          
          /* Determine Shape: Active is rounded, Hover is rounded, Default is circle */
          ${active ? 'rounded-discord' : 'rounded-[50%] group-hover:rounded-discord'}

          /* Determine Colors */
          ${active 
            ? 'bg-brand text-white' 
            : 'bg-discord-sidebar text-discord-text group-hover:bg-brand group-hover:text-white'
          }
      `}>
        {label}
      </button>
    </div>
  );
}