import { NextRequest, NextResponse } from 'next/server';
import { serverFetch } from '@/lib/auth/server_fetch';
import { isNextRedirect } from '@/lib/utils/errors';

// Backend URL from env
const INTERNAL_API_ENDPOINT = process.env.INTERNAL_API_ENDPOINT;

async function handler(request: NextRequest, { params }: { params: Promise<{ path: string[] }>}) {
  // 1. Reconstruct the path (e.g., /api/proxy/users/me -> users/me)
  const path = (await params).path.join('/');
  const query = request.nextUrl.search;
  const targetUrl = `${INTERNAL_API_ENDPOINT}/${path}${query}`;

  // 2. Prepare headers
  const headers = new Headers(request.headers);
  headers.delete('host');
  headers.delete('connection'); 

  try {
    // 3. Forward the request to backend and deal with auth
    const backendResponse = await serverFetch(targetUrl, {
      method: request.method,
      headers: headers,
      // Only pass body if it's not a GET/HEAD request
      body: (request.method !== 'GET' && request.method !== 'HEAD') ? request.body : undefined,
      // @ts-ignore
      duplex: 'half', 
    });

    // 4. Return the Backend's response to the Client
    return new Response(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: backendResponse.headers,
    });

  } catch (error) {
    if (isNextRedirect(error)) throw error;
    console.error("Proxy Error:", error);
    return NextResponse.json(
      { message: "Failed to connect to backend", detail: String(error) }, 
      { status: 502 }
    );
  }
}

// Support all common HTTP methods
export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;