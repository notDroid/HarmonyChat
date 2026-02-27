import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { SESSION_SETTINGS } from './settings/session'

export function proxy(request: NextRequest) {
  // Check if user has a token (either access or refresh)
  const token = request.cookies.get(SESSION_SETTINGS.ACCESS_TOKEN_COOKIE_NAME)?.value || request.cookies.get(SESSION_SETTINGS.REFRESH_TOKEN_COOKIE_NAME)?.value;
  const { pathname } = request.nextUrl

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