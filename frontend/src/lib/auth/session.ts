"use server"

import { cookies } from 'next/headers';
import { SESSION_SETTINGS } from '@/settings/session';
import { Token } from '../api/model';

export async function isRefreshUrl(url: string) {
  return url.includes(SESSION_SETTINGS.REFRESH_ENDPOINT);
}

export async function clearSession() {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME);
  cookieStore.delete(SESSION_SETTINGS.REFRESH_TOKEN_COOKIE_NAME);
}

export async function getAccesstToken() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME)?.value;
  return token;
}

export async function getRefreshToken() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_SETTINGS.REFRESH_TOKEN_COOKIE_NAME)?.value;
  return token;
} 

export async function injectToken(options: RequestInit, token: string): Promise<RequestInit> {
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${token}`);

  const combinedOptions: RequestInit = {
    ...options,
    headers
  };
  return combinedOptions;
}

export async function setToken(token: Token) {
  // Expiration is in seconds, get expiration and convert to milliseconds for Date constructor
  const expiresAt = token.expiration ? new Date(token.expiration * 1000) : undefined;

  // Set the Cookie
  const cookieStore = await cookies();
  cookieStore.set(token.token_type, token.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    expires: expiresAt,
  });
}