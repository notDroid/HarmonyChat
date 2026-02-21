import { useQueryClient, InfiniteData } from '@tanstack/react-query';
import { CHAT_PANEL_SETTINGS } from '@/settings/chat_panel';
import { ChatHistoryResponse } from "@/lib/api/model";
import { UIMessage } from "../ui/message";

export function useChatCache(chat_id: string) {
  const queryClient = useQueryClient();
  const queryKey = [CHAT_PANEL_SETTINGS.QUERY_KEY, chat_id];

  const insertOrUpdateMessage = (newMessage: UIMessage) => {
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (oldData) => {
      if (!oldData) return oldData;

      let messageReplaced = false;
			
			// Try to find and replace the message in the existing pages
      const newPages = oldData.pages.map(page => {
        const updatedMessages = page.messages.map(msg => {
          const m = msg as UIMessage;
          
          if (m.ulid === newMessage.ulid || (m.client_uuid && m.client_uuid === newMessage.client_uuid)) {
            messageReplaced = true;
            return { ...m, ...newMessage, status: newMessage.status || 'sent' };
          }
          return m;
        });
        return { ...page, messages: updatedMessages };
      });
			
			// If the message wasn't found and replaced, it means it's a new message that should be added to the end of the first page
			// It will be sorted correctly later when we flatten and sort all messages
      if (!messageReplaced) {
        newPages[0] = {
          ...newPages[0],
          messages: [...newPages[0].messages, { ...newMessage, status: newMessage.status || 'sent' }]
        };
      }

      return { ...oldData, pages: newPages };
    });
  };

  const updateMessageStatus = (client_uuid: string, status: 'pending' | 'error' | 'sent') => {
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(queryKey, (oldData) => {
      if (!oldData) return oldData;

			// Update the status of the message with the matching client_uuid
      const newPages = oldData.pages.map(page => ({
        ...page,
        messages: page.messages.map(msg => {
          const m = msg as UIMessage;
          if (m.client_uuid === client_uuid) {
            return { ...m, status };
          }
          return m;
        })
      }));

      return { ...oldData, pages: newPages };
    });
  };

  return {
    queryKey,
    queryClient,
    insertOrUpdateMessage,
    updateMessageStatus
  };
}