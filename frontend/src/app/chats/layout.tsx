import ServerSidebar from "@/features/server_sidebar/ui/server_sidebar";

export default function ChatsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="fixed flex h-screen w-full">
      <ServerSidebar />
      {children}
    </div>
  );
}