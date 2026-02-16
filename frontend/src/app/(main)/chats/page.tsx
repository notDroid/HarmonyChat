export default function ChatsWelcomePage() {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center bg-app-bg text-app-text p-6">
      
      {/* Decorative Empty State */}
      <div className="flex max-w-lg flex-col items-center text-center">
        
        {/* Animated/Static Graphic */}
        <div className="mb-6 rounded-full bg-app-server p-6 shadow-sm border border-app-outline">
          <svg 
            className="h-12 w-12 text-app-muted" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor" 
            strokeWidth="1.5"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
          </svg>
        </div>

        <h2 className="mb-2 text-2xl font-semibold">
          Welcome to Harmony
        </h2>
        
        <p className="max-w-xs text-app-muted">
          Select a chat from the sidebar to start messaging, or check back later for new invites.
        </p>

        {/* Optional Hint Pill */}
        <div className="mt-8 rounded-full border border-app-outline bg-app-sidebar px-4 py-1.5 text-xs font-medium text-app-muted">
          <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-brand animate-pulse"></span>
          You are online
        </div>
      </div>
    </div>
  );
}