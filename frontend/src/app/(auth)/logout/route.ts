import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  // 1. Delete the bad cookie
  (await cookies()).delete('session_token');

  // 2. Redirect to login (now safely without a cookie)
  return NextResponse.redirect(new URL('/login', request.url));
}