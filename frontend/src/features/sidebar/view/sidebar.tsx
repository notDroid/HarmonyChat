import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query';
import { NetworkError } from "@/lib/utils/errors";

import ServerListWrapper from "../components/sidebar";

import { prefetchSidebarChats } from '../api/cache';

export default async function ServerSidebarView({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient();

    try {
        // Attempt to Prefetch the sidebar chats to populate the cache
        await prefetchSidebarChats(queryClient);
    } catch (error) {
        if (!(error instanceof NetworkError)) {
            throw error;
        }
        // Let client render sidebar and handle the error gracefully
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