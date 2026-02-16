import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

// Your backend URL from env
const INTERNAL_API_URL = process.env.INTERNAL_API_URL;

async function handler(request: NextRequest, { params }: { params: { path: string[] } }) {
  // 1. Reconstruct the actual path (e.g., /api/proxy/users/me -> users/me)
  const path = (await params).path.join('/');
  const query = request.nextUrl.search; // Keep query parameters (e.g., ?limit=10)
  const targetUrl = `${INTERNAL_API_URL}/${path}${query}`;

  // 2. Prepare headers
  const headers = new Headers(request.headers);
  headers.delete('host'); // prevent host mismatch errors
  headers.delete('connection'); 

  // 3. Inject Auth Token from Cookie (BFF Pattern)
  // This securely moves the token from a cookie to a Header
  const cookieStore = await cookies();
  const token = cookieStore.get('session_token')?.value;
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  try {
    // 4. Forward the request to the actual Backend
    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers: headers,
      // Only pass body if it's not a GET/HEAD request
      body: (request.method !== 'GET' && request.method !== 'HEAD') ? request.body : undefined,
      // @ts-ignore - Required for some Node versions to proxy request bodies efficiently
      duplex: 'half', 
    });

    // 5. Return the Backend's response to the Client
    // We stream the body directly to support large data sets
    return new Response(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: backendResponse.headers,
    });

  } catch (error) {
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