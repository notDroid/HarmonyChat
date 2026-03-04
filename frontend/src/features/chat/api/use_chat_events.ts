import { useCentrifugeSubscription } from '@/features/websocket/use_cent_sub';
import { useCallback } from 'react';

export function useChatEvents(chat_id: string, onEvent: (event: any) => void) {
  const handleEvent = useCallback((ctx: any) => {
    onEvent(ctx.data);
  }, [onEvent]);

  useCentrifugeSubscription(`chat:${chat_id}`, handleEvent);
}