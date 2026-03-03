import { NextResponse } from 'next/server';
import { refreshAction } from '@/features/auth/actions/refresh';
import { clearSession, clearAccessToken, setTokenWithResponse } from '@/lib/auth/session';
import { SESSION_SETTINGS } from '@/settings/session';

import { NetworkError } from '@/lib/utils/errors';

// This handles 401 errors to quickly refresh tokens regardless of where they come from (client or server components)
// The proxy middleware will usually handle refreshing tokens automatically (99% of the time),
// but there is a race condition where we get a 401 before the proxy has a chance to refresh
export async function refresh(request: Request) {
  const url = new URL(request.url);
  const nextUrl = url.searchParams.get('next') || ''; // we always expect a next param
  console.log(`Received request to /api/auth/refresh with next=${nextUrl}`);

  try {
    const tokens = await refreshAction(); 
    console.log('Token refresh successful in /api/auth/refresh route');
    const response = NextResponse.redirect(new URL(nextUrl, request.url));

    for (const token of tokens) {
      setTokenWithResponse(response, token);
    }

    return response;
  } catch (error) {
    if (error instanceof NetworkError) {
      console.error('Network error during refresh, keeping session intact', error);
      // This triggers proxy middleware to attempt refresh again on next request
      // allowing for transient network issues to resolve without logging the user out
      const response = NextResponse.redirect(new URL(nextUrl, request.url));
      response.cookies.delete(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME); // Clear access token to trigger refresh logic on next request
      return response;
    }

    console.warn('Auth error during refresh, clearing session and redirecting to logout', error instanceof Error ? error.message : String(error));
    const response = NextResponse.json({}, { status: 401 });
    response.cookies.delete(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME);
    response.cookies.delete(SESSION_SETTINGS.REFRESH_TOKEN_COOKIE_NAME);
    return response;
  }
}

export const GET = refresh;
export const POST = refresh;
export const PUT = refresh;
export const PATCH = refresh;
export const DELETE = refresh;