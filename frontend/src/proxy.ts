import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server';

import { SESSION_SETTINGS } from './settings/session'
import { refreshAction } from '@/features/auth/actions/refresh';
import { isNextRedirect, NetworkError } from './lib/utils/errors';

export async function proxy(request: NextRequest) {
  const access_token = request.cookies.get(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME)?.value;
  const refresh_token = request.cookies.get(SESSION_SETTINGS.REFRESH_TOKEN_COOKIE_NAME)?.value;
  const token = access_token || refresh_token;
  const { pathname } = request.nextUrl

  // If we have a refresh token but no access token, and we're not already trying to refresh, attempt to refresh
  if (refresh_token && !access_token) {
    console.log(`Attempting token refresh in proxy middleware for request to ${pathname}`);
    try {
      await refreshAction();
      console.log(`Token refresh successful in proxy middleware for request to ${pathname}`);
      return NextResponse.next();
    } catch (error) {
      console.log(`Token refresh failed in proxy middleware: ${error instanceof Error ? error.message : String(error)}`);
      if (isNextRedirect(error)) throw error;
      if (!(error instanceof NetworkError)) {
        // If refresh fails, clear the refresh token and redirect to login
        const loginUrl = new URL('/login', request.url)
        loginUrl.searchParams.set('next', pathname)
        return NextResponse.redirect(loginUrl)
      }
    }
  }

  // If user is on a protected path and has no token, kick them out
  if (!token && pathname.startsWith('/chats')) {
    const loginUrl = new URL('/login', request.url)
    // Return them to where they were trying to go after they log in
    loginUrl.searchParams.set('next', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // If user is on login page but HAS a token, send them to chats
  if (token && pathname === '/login') {
    return NextResponse.redirect(new URL('/chats', request.url))
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/chats/:path*', '/login'],
}