import { useCentrifugeSubscription } from '@/lib/api/ws/use_cent_sub';
import { ChatEvent } from '@/lib/api/ws/model';

export function useChatEvents(chat_id: string, onEvent: (event: ChatEvent) => void) {
  useCentrifugeSubscription(`chat:${chat_id}`, (ctx) => {
    onEvent(ctx.data as ChatEvent);
  });
}