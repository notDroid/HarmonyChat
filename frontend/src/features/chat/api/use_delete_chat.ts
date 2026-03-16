import { useMutation } from '@tanstack/react-query';
import { deleteChatApiV1ChatsChatIdDelete } from '@/lib/api/chat/chat';
import { useSidebarCache } from '@/features/sidebar/api/cache';
import { useRouter } from 'next/navigation';
import { ApiError } from '@/lib/utils/errors';

export function useDeleteChat() {
  const { removeChat } = useSidebarCache();
  const router = useRouter();

  return useMutation({
    mutationFn: async (chat_id: string) => {
      await deleteChatApiV1ChatsChatIdDelete(chat_id);
      return chat_id;
    },
    onSuccess: (chat_id) => {
      removeChat(chat_id);
      router.push('/chats');
    },
    onError: (error) => {
      const msg = error instanceof ApiError ? error.message : "Failed to delete chat.";
      console.error(msg);
    }
  });
}