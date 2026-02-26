export default function ChatHeaderSkeleton() {
    return (
        <div className="
            w-full h-header 
            flex items-center
            bg-app-bg
            border-b border-app-outline
            shrink-0
            px-4
        ">
            <div className="flex flex-col w-full">
                {/* Title Skeleton: mimics text-lg leading-tight */}
                <div className="h-5 w-40 bg-app-loading rounded-md animate-pulse" />
                
                {/* Description Skeleton: mimics text-xs h-4 mt-1 */}
                <div className="h-3 w-64 bg-app-loading rounded-sm animate-pulse mt-2" />
            </div>
        </div>
    );
}