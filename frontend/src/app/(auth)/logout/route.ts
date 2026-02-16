import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  // Delete the bad cookie
  (await cookies()).delete('session_token');

  // Redirect to login (now safely without a cookie)
  return NextResponse.redirect(new URL('/login', request.url));
}