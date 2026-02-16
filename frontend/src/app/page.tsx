import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-app-bg text-app-text transition-colors duration-200">
      
      {/* Main Card */}
      <div className="w-full max-w-md space-y-8 px-4 text-center">
        
        {/* Hero Section */}
        <div className="space-y-4">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-app-sidebar border border-app-outline shadow-sm">
            {/* Simple Logo Icon */}
            <svg 
              className="h-10 w-10 text-brand" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Harmony<span className="text-brand">Chat</span>
          </h1>
          
          <p className="text-lg text-app-muted">
            A simple, fast, and secure way to connect with your friends.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/login"
            className="inline-flex h-12 items-center justify-center rounded-lg bg-brand px-8 text-sm font-semibold text-white shadow-sm transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
          >
            Log in
          </Link>
          
          <Link
            href="/signup"
            className="inline-flex h-12 items-center justify-center rounded-lg border border-app-outline bg-app-sidebar px-8 text-sm font-semibold text-app-text shadow-sm transition-all hover:bg-app-hover focus:outline-none focus:ring-2 focus:ring-app-outline focus:ring-offset-2"
          >
            Sign up
          </Link>
        </div>
      </div>

      {/* Footer */}
      <div className="absolute bottom-8 text-xs text-app-muted">
        &copy; {new Date().getFullYear()} HarmonyChat. All rights reserved.
      </div>
    </div>
  );
}