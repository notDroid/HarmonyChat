import ServerSidebar from "@/components/layout/server_sidebar";

export default function ChatsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <ServerSidebar />
      <div className="ml-sidebar">{children}</div>
    </div>
  );
}