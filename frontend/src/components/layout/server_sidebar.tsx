import ServerIcon from "@/components/ui/server_icon";

export default function ServerSidebar() {
  return (
    <nav className="
        flex-none
        top-0 left-0 h-screen
        w-sidebar
        bg-discord-server 
        flex flex-col items-center
        overflow-y-auto scrollbar-hide
        py-3 gap-3
    ">
      <ServerIcon label="A" active />
      <ServerIcon label="B" unread />
      <ServerIcon label="C" />
      
      <ServerIcon label="D" unread />
      <ServerIcon label="E" />
    </nav>
  );
}