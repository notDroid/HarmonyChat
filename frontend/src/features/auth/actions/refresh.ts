"use server";

import { Token } from '@/lib/api/model/token';
import { setToken, getRefreshToken } from '@/lib/auth/session';
import { refreshApiV1AuthRefreshPost } from '@/lib/api/auth/auth';
import { RefreshRequest } from '@/lib/api/model/refreshRequest';

export async function refreshAction() {
  // Create request
  const refreshToken = await getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  const request: RefreshRequest = {
    refresh_token: refreshToken,
  };

  // Call refresh endpoint
  const res = await refreshApiV1AuthRefreshPost(request);
  
  // Set tokens
  const tokens = (res.data as Token[]);
  for (const token of tokens) {
    await setToken(token);
  }
}