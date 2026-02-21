import { useMutation, InfiniteData } from '@tanstack/react-query';
import { ChatHistoryResponse } from '@/lib/api/model';
import { sendMessageApiV1ChatsChatIdPost } from '@/lib/api/chat/chat';
import { UIMessage } from '../ui/message';
import { useChatCache } from './cache'; // Import your new hook

export default function useSendMessage(chat_id: string) {
  const { queryClient, queryKey, insertOrUpdateMessage, updateMessageStatus } = useChatCache(chat_id);

  return useMutation({
    mutationFn: async ({ content, client_uuid }: { content: string, client_uuid: string }) => {
      const result = await sendMessageApiV1ChatsChatIdPost(chat_id, { content, client_uuid });
      return result.data; 
    },
    
    onMutate: async ({ content, client_uuid }) => {
      // Stop background fetches and take a snapshot of the current cache state for this chat
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<InfiniteData<ChatHistoryResponse>>(queryKey);

      insertOrUpdateMessage({
        chat_id,
        content,
        ulid: client_uuid,
        client_uuid,
        timestamp: new Date().toISOString(),
        user_id: "me", 
        status: 'pending'
      });

      // Return context with the previous data and client_uuid for potential rollback or error handling
      return { previousData, client_uuid };
    },

    onError: (err, variables, context) => {
      // Flag the message as failed in the cache
      if (context?.client_uuid) {
        updateMessageStatus(context.client_uuid, 'error');
      }
    },

    onSuccess: (realMessage) => {
      // Swap out the pending message for the real one
      insertOrUpdateMessage(realMessage as UIMessage);
    }
  });
}