import { NetworkError, ApiError } from "@/lib/api/errors";
import { isNextRedirect } from "@/lib/api/utils";
import ErrorScreen from "@/components/error";

import ServerListWrapper from "../components/sidebar";
import getMyChats from "../api/get_my_chats";


export default async function ServerSidebarView( { children }: { children: React.ReactNode } ) {
    let chat_id_list: string[] | undefined;
    
    try {
        chat_id_list = await getMyChats();
    } catch (error) {
        if (isNextRedirect(error)) {
            throw error; // Let the redirect happen
        }
        
        if (error instanceof NetworkError) {
            // For network errors, we can treat it as "still loading" since it might be a temporary issue
            chat_id_list = undefined;
        }
        else if (error instanceof ApiError) {
            return <ErrorScreen message={error.message || 'Unable to load chats.'} />;
        }
        else {
            return <ErrorScreen message={'Something went wrong. Please try again later.'} />;
        }
    }

    return (
        <ServerListWrapper initial_chat_id_list={chat_id_list} children={children} />
    );
}