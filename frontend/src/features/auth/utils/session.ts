"use server"

import { cookies } from 'next/headers';
import { SESSION_SETTINGS } from '@/settings/session';

export async function clearSession() {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME);
}