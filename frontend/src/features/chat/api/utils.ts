import { InfiniteData } from '@tanstack/react-query';
import { ChatHistoryResponse } from "@/lib/api/model";
import { UIMessage } from "../ui/message"; // [cite: 666]

// Inserts a new message or updates an existing one if the client_uuid or ulid matches.
// Defaults new messages to 'sent' status if not provided, but can be overridden (e.g. for optimistic updates).
export function insertOrUpdateMessage(
  oldData: InfiniteData<ChatHistoryResponse> | undefined,
  newMessage: UIMessage
): InfiniteData<ChatHistoryResponse> | undefined {
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

	// Otherwise if we didn't find a match, we can assume it's a new message and add it to the end of the first page (sorted later)
  if (!messageReplaced) {
    newPages[0] = {
      ...newPages[0],
      messages: [...newPages[0].messages, { ...newMessage, status: newMessage.status || 'sent' }]
    };
  }

  return { ...oldData, pages: newPages };
}

// Used to flag an optimistic message as an error if the API fails.
export function updateMessageStatus(
  oldData: InfiniteData<ChatHistoryResponse> | undefined,
  client_uuid: string,
  status: 'pending' | 'error' | 'sent'
): InfiniteData<ChatHistoryResponse> | undefined {
  if (!oldData) return oldData;

	// Iterate through pages and update status of the message with the matching client_uuid
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
}