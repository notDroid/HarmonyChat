import { useMutation } from '@tanstack/react-query';
import { leaveChatApiV1ChatsChatIdLeavePost } from '@/lib/api/chat/chat';
import { useSidebarCache } from '@/features/sidebar/api/cache';
import { useRouter } from 'next/navigation';
import { ApiError } from '@/lib/utils/errors';

export function useLeaveChat() {
    const { removeChat } = useSidebarCache();
    const router = useRouter();

    return useMutation({
        mutationFn: async (chat_id: string) => {
            await leaveChatApiV1ChatsChatIdLeavePost(chat_id);
            return chat_id;
        },
        onSuccess: (chat_id) => {
            removeChat(chat_id);
            router.push('/chats');
        },
        onError: (error) => {
            const msg = error instanceof ApiError ? error.message : "Failed to leave chat.";
            console.error(msg);
        }
    });
}