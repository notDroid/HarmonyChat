"use server";

import { Token } from '@/lib/api/model/token';
import { setToken } from '@/lib/auth/session';
import { refreshApiV1AuthRefreshPost } from '@/lib/api/auth/auth';

export async function refreshAction() {
  // Call refresh endpoint
  const res = await refreshApiV1AuthRefreshPost();
  
  // Set tokens
  const tokens = (res.data as Token[]);
  for (const token of tokens) {
    await setToken(token);
  }
}