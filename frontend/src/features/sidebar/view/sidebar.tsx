import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query';
import { NetworkError, ApiError } from "@/lib/utils/errors";
import { isNextRedirect } from "@/lib/utils/utils";
import ErrorScreen from "@/components/error";

import ServerListWrapper from "../components/sidebar";
import getMyChats from "../api/get_my_chats";

import { SIDEBAR_SETTINGS } from '@/settings/sidebar';

export default async function ServerSidebarView({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient();

    try {
        // Attempt to Prefetch the "myChats" query on the server
        await queryClient.fetchQuery({
            queryKey: [SIDEBAR_SETTINGS.QUERY_KEY],
            queryFn: getMyChats,
        });
    } catch (error) {
        if (isNextRedirect(error)) throw error;

        if (error instanceof NetworkError) {
            // If it's a network error, we do nothing. 
            // The queryClient cache remains empty. When we pass it to the client, 
            // the client will see no data and naturally try to fetch it itself.
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