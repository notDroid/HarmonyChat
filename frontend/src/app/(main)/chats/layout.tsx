import ChatScreen from "@/components/chat_view";
import { CentrifugeProvider } from "@/features/websocket/cent_provider";

export default function ChatsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <CentrifugeProvider>
      <ChatScreen>{children}</ChatScreen>
    </CentrifugeProvider>
  );
}