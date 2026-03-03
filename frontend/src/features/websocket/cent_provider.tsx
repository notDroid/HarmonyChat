'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Centrifuge } from 'centrifuge';

const CENT_URL = process.env.NEXT_PUBLIC_CENTRIFUGE_URL!;

const CentrifugeContext = createContext<Centrifuge | null>(null);

export function CentrifugeProvider({ children }: { children: ReactNode }) {
  const [centrifuge, setCentrifuge] = useState<Centrifuge | null>(null);

  useEffect(() => {
    const client = new Centrifuge(CENT_URL);

    client.connect();
    setCentrifuge(client);

    return () => {
      client.disconnect();
    };
  }, []);

  return (
    <CentrifugeContext.Provider value={centrifuge}>
      {children}
    </CentrifugeContext.Provider>
  );
}

export function useCentrifuge() {
  const ctx = useContext(CentrifugeContext);
  if (ctx === undefined) {
    throw new Error('useCentrifuge must be used within a CentrifugeProvider');
  }
  return ctx;
}