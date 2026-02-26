export default function CreateChatButton({ onClick }: { onClick: () => void }) {
  return (<>
    { /* Create Chat Button */ }
    <div className="relative group flex items-center justify-center w-full my-1">
      <button 
        onClick={onClick}
        aria-label="Create new chat"
        className={`
          h-server-icon w-server-icon
          flex items-center justify-center
          transition-all duration-200 ease-linear
          shadow-sm
          overflow-hidden
          rounded-[50%] group-hover:rounded-server-icon-expanded
          bg-app-sidebar text-brand group-hover:bg-brand group-hover:text-white
        `}
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          fill="none" 
          viewBox="0 0 24 24" 
          strokeWidth={2} 
          stroke="currentColor" 
          className="w-6 h-6"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
    </div>
    
    { /* Separator line */ }
    <div className="w-9 h-0.5 bg-app-outline rounded-full mx-auto shrink-0" />
  </>);
}