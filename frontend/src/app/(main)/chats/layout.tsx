import ServerSidebarView from "@/features/sidebar/view/sidebar";
import { Suspense } from "react";
import LoadingScreen from "@/components/loading";

import { QueryClient, dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { prefetchCurrentUser } from '@/features/user/api/cache';
import { ApiError, NetworkError, isNextRedirect } from "@/lib/utils/errors";
import ErrorScreen from "@/components/error";

export default async function ChatsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const queryClient = new QueryClient();
  
  try {
      // Attempt to prefetch user metdata
      await prefetchCurrentUser(queryClient);
  } catch (error) {
      if (isNextRedirect(error)) throw error;
      
      if (error instanceof NetworkError) {
          // Retry on the client side
      }
      else if (error instanceof ApiError) {
          return <ErrorScreen message={error.message || 'Unable to load chats.'} />;
      }
      else {
          return <ErrorScreen message={'Something went wrong. Please try again later.'} />;
      }
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Suspense fallback={<LoadingScreen />}>
        <ServerSidebarView children={children} />
      </Suspense>
    </HydrationBoundary>
  );
}