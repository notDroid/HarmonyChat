export interface ChatHeaderProps {
    title: string;
    description?: string;
}

export function ChatHeader({ metadata }: { metadata?: ChatHeaderProps }) {
    return (
        <div className="
            w-full h-header 
            flex items-center
            bg-app-bg
            border-b border-app-outline
            shrink-0
            px-4
            py-8
        ">
            {/* Added w-full to ensure truncation works properly if it gets wide */}
            <div className="flex flex-col w-full">
                
                {/* leading-tight removes awkward invisible padding above/below the text */}
                <h1 className="text-lg font-semibold text-app-text leading-tight">
                  {metadata?.title || "Untitled Chat"}
                </h1>
                
                {/* 1. h-4 and mt-1 ensure this space is ALWAYS reserved.
                  2. text-xs creates better visual hierarchy.
                  3. truncate ensures long text doesn't wrap and break the header height.
                */}
                <p className="text-xs text-app-text opacity-70 h-4 mt-1 truncate">
                    {metadata?.description || ""}
                </p>

            </div>
        </div>
    );
}