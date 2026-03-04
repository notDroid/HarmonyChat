import { useCentrifugeSubscription } from '@/features/websocket/use_cent_sub';
import { ChatEvent } from '@/features/websocket/model';
import { useCallback } from 'react';

export function useChatEvents(chat_id: string, onEvent: (event: ChatEvent) => void) {
  const handleEvent = useCallback((ctx: any) => {
    onEvent(ctx.data as ChatEvent);
  }, [onEvent]);

  useCentrifugeSubscription(`chat:${chat_id}`, handleEvent);
}