'use client';

import ErrorScreen from "@/components/error";

export default function HomeError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const message = error.message || "Unable to load. Please try again later.";
  return <ErrorScreen message={message} />;
}