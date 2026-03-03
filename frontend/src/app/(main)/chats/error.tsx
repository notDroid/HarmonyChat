"use client";

import ErrorScreen from "@/components/error";

export default function ChatError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const message = error.message || "Unable to load chat. Please try again later.";
  return <ErrorScreen message={message} />;
}

