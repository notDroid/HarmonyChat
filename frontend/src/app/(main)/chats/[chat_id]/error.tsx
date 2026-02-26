'use client';

import ErrorChatPanel from "@/features/chat/ui/error";

export default function ChatError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const message = error.message || "Unable to load chat. Please try again later.";
  return <ErrorChatPanel message={message} />;
}