import { useMutation, useQueryClient, InfiniteData } from '@tanstack/react-query';
import { CHAT_PANEL_SETTINGS } from '@/settings/chat_panel';
import { ChatHistoryResponse } from '@/lib/api/model';
import { sendMessageApiV1ChatsChatIdPost } from '@/lib/api/chat/chat';
import { UIMessage } from '../ui/message';
import { insertOrUpdateMessage, updateMessageStatus } from './utils';

export default function useSendMessage(chat_id: string) {
  const queryClient = useQueryClient();
  const queryKey = [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id];

  return useMutation({
    mutationFn: async ({ content, client_uuid }: { content: string, client_uuid: string }) => {
      const result = await sendMessageApiV1ChatsChatIdPost(chat_id, { content, client_uuid });
      return result.data; 
    },
    
    onMutate: async ({ content, client_uuid }) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<InfiniteData<ChatHistoryResponse>>(queryKey);

      // Create the fake optimistic UI message
      const optimisticMessage: UIMessage = {
        chat_id,
        content, 
        ulid: client_uuid, // Temporary fake ID
        client_uuid,
        timestamp: new Date().toISOString(), 
        user_id: "me", // TODO: Find a better way to get the current user's ID
        status: 'pending'
      };
      
      // Optimistically add the message to screen immediately
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (old) => 
        insertOrUpdateMessage(old, optimisticMessage)
      );

      return { previousData, client_uuid };
    },

    onError: (err, variables, context) => {
      // Mark the optimistic message as errored so the UI can reflect the failure and allow retrying
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (old) => {
        if (!old) return context?.previousData;
        return updateMessageStatus(old, context!.client_uuid, 'error');
      });
    },

    onSuccess: (realMessage, variables, context) => {
      // Replace the optimistic message with the real message from the server (which has the real ULID and any other server-generated fields)
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (old) => 
        insertOrUpdateMessage(old, realMessage as UIMessage)
      );
    }
  });
}