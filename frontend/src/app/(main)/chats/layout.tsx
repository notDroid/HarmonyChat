import ServerSidebarView from "@/features/sidebar/view/sidebar";
import { Suspense } from "react";
import LoadingScreen from "@/components/loading";

export default function ChatsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <ServerSidebarView children={children} />
    </Suspense>
  );
}