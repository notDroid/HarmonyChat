import Header from "@/components/ui/header"

export default function ChatWindow(
    { children }: { children: React.ReactNode }
) {
    return (
        <div className="flex h-full w-full flex-col min-w-0 ">
            <Header />
            {children}
        </div>
    );
}