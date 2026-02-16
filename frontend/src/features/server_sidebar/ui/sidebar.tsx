export default function ServerSidebar({ children }: { children: React.ReactNode }) {
  return (
    <nav className="
        flex-none
        top-0 left-0 h-screen
        w-sidebar
        bg-app-server 
        flex flex-col items-center
        overflow-y-auto scrollbar-hide
        py-3 gap-3
        border-r
        border-app-outline
    ">
      {children}
    </nav>
  );
}