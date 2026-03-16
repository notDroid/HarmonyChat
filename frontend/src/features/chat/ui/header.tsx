export interface ChatHeaderProps {
    title: string;
    description?: string;
}

export function ChatHeader({ metadata, children }: { metadata?: ChatHeaderProps, children?: React.ReactNode }) {
    return (
        <div className="w-full h-header flex items-center justify-between bg-app-bg border-b border-app-outline shrink-0 px-4 py-8">
            <div className="flex flex-col w-full overflow-hidden">
                <h1 className="text-lg font-semibold text-app-text leading-tight truncate">
                  {metadata?.title || "Untitled Chat"}
                </h1>
                <p className="text-xs text-app-text opacity-70 h-4 mt-1 truncate">
                    {metadata?.description || ""}
                </p>
            </div>
            
            {/* Render the right-aligned actions (Info button) */}
            {children && (
              <div className="ml-4 flex items-center shrink-0">
                {children}
              </div>
            )}
        </div>
    );
}