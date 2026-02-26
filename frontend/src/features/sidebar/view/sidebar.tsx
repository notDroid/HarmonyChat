import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query';
import { NetworkError, ApiError, isNextRedirect } from "@/lib/utils/errors";
import ErrorScreen from "@/components/error";

import ServerListWrapper from "../components/sidebar";

import { prefetchSidebarChats } from '../api/cache';

export default async function ServerSidebarView({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient();

    try {
        // Attempt to Prefetch the sidebar chats to populate the cache
        await prefetchSidebarChats(queryClient);
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

    // Dehydrate the queryClient state and pass it into the HydrationBoundary
    return (
        <HydrationBoundary state={dehydrate(queryClient)}>
            <ServerListWrapper>
                {children}
            </ServerListWrapper>
        </HydrationBoundary>
    );
}