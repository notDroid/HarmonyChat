import { useEffect, useState } from 'react';
import { useCentrifuge } from './cent_provider';

export function useCentrifugeSubscription(channel: string | null, onEvent: (ctx: any) => void) {
  const centrifuge = useCentrifuge();
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    if (!centrifuge || !channel) return;

    const sub = centrifuge.newSubscription(channel);

    sub.on('publication', onEvent);
    sub.on('subscribed', () => setIsSubscribed(true));
    sub.on('unsubscribed', () => setIsSubscribed(false));

    sub.subscribe();

    return () => {
      sub.removeAllListeners();
      sub.unsubscribe();
    };
  }, [centrifuge, channel, onEvent]);

  return { isSubscribed };
}