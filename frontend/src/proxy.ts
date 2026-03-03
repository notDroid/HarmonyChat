import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server';

import { SESSION_SETTINGS } from './settings/session'
import { refreshAction } from '@/features/auth/actions/refresh';
import { NetworkError } from './lib/utils/errors';
import { setTokenWithResponse } from '@/lib/auth/session';

export async function proxy(request: NextRequest) {
  // Reading cookies via NextRequest (Correct for Middleware)
  const access_token = request.cookies.get(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME)?.value;
  const refresh_token = request.cookies.get(SESSION_SETTINGS.REFRESH_TOKEN_COOKIE_NAME)?.value;
  const token = access_token || refresh_token;
  const { pathname } = request.nextUrl

  if (refresh_token && !access_token) {
    console.log(`Attempting token refresh in proxy middleware for request to ${pathname}`);
    try {
      const tokens = await refreshAction();
      const response = NextResponse.next();
      for (const token of tokens) {
        setTokenWithResponse(response, token);
      }
      console.log(`Token refresh successful in proxy middleware for request to ${pathname}`);
      return response;
    } catch (error) {
      console.log(`Token refresh failed in proxy middleware: ${error instanceof Error ? error.message : String(error)}`);
      
      if (!(error instanceof NetworkError)) {
        const loginUrl = new URL('/login', request.url)
        loginUrl.searchParams.set('next', pathname)
        
        // 1. Create the response object
        const response = NextResponse.redirect(loginUrl)
        
        // 2. Clear the cookies on the NextResponse object
        response.cookies.delete(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME)
        response.cookies.delete(SESSION_SETTINGS.REFRESH_TOKEN_COOKIE_NAME)
        
        return response
      }
    }
  }

  if (!token && pathname.startsWith('/chats')) {
    console.log(`No token found for request to ${pathname}, redirecting to login`);
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('next', pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (token && pathname === '/login') {
    console.log(`Token found for request to /login, redirecting to /chats`);
    return NextResponse.redirect(new URL('/chats', request.url))
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/chats/:path*', '/login'],
}