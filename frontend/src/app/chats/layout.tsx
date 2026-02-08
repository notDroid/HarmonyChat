import ServerSidebar from "@/components/layout/server_sidebar";

export default function ChatsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen w-full">
      <ServerSidebar />
      <div className="h-full w-full">
        {children}
      </div>
    </div>
  );
}