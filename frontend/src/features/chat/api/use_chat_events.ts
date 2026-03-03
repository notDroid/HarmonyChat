import { useCentrifugeSubscription } from '@/features/websocket/use_cent_sub';
import { ChatEvent } from '@/features/websocket/model';

export function useChatEvents(chat_id: string, onEvent: (event: ChatEvent) => void) {
  useCentrifugeSubscription(`chat:${chat_id}`, (ctx) => {
    onEvent(ctx.data as ChatEvent);
  });
}