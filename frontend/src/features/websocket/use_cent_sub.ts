import { useEffect, useState } from 'react';
import { useCentrifuge } from './cent_provider';

export function useCentrifugeSubscription(channel: string | null, onEvent: (ctx: any) => void) {
  const centrifuge = useCentrifuge();
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    if (!centrifuge || !channel) return;

    // Get the existing subscription, or create a new one if it doesn't exist
    const sub = centrifuge.getSubscription(channel) || centrifuge.newSubscription(channel);

    sub.on('publication', onEvent);
    sub.on('subscribed', () => setIsSubscribed(true));
    sub.on('unsubscribed', () => setIsSubscribed(false));

    sub.subscribe();

    return () => {
      sub.removeAllListeners();
      sub.unsubscribe();
      centrifuge.removeSubscription(sub); 
    };
  }, [centrifuge, channel, onEvent]);

  return { isSubscribed };
}