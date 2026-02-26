'use client';

import { ApiError, AuthRedirectError, isNextRedirect } from '@/lib/utils/errors';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

const DEFAULT_RETRY_COUNT = 3;

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        retry: (failureCount, error) => {
          if (isNextRedirect(error)) throw error;
          if (error instanceof AuthRedirectError) throw error;

          if (error instanceof ApiError) {
            return false; 
          }
          
          return failureCount < DEFAULT_RETRY_COUNT;
        },
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}