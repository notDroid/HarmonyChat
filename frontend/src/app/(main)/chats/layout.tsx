import ServerSidebarView from "@/features/sidebar/view/sidebar";

export default function ChatsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ServerSidebarView children={children} />
  );
}