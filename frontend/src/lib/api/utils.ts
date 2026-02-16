import { isRedirectError } from 'next/dist/client/components/redirect-error';
import { ApiError, NetworkError, AuthRedirectError } from './errors';
import { redirect } from 'next/navigation';

const isServer = typeof window === 'undefined';

export function isNextRedirect(error: unknown) {
  return isRedirectError(error);
}

export const getBaseUrl = () => {
  if (isServer) {
    return process.env.INTERNAL_API_URL; 
  } else {
    return '/api/proxy'; 
  }
};

export async function getAuthHeader() {
	if (!isServer) return {}; // Don't include auth headers on client-side requests
	const { cookies } = await import('next/headers'); 
  const cookieStore = await cookies();
  const token = cookieStore.get('session_token')?.value;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleAuthError(requestUrl: string) {
  // Ignore login endpoint failures
  if (requestUrl.includes('/auth')) return;

  if (typeof window === 'undefined') {
    // SERVER SIDE: Use Next.js redirect (throws its own internal error)
    redirect('/login');
  } else {
    // CLIENT SIDE:
    // Force a hard navigation (clears memory/state)
    window.location.href = '/login';
    
    // Throw specific error to halt the current function execution
    throw new AuthRedirectError();
  }
}

export async function fetchErrorWrapper<T>(url: string, options?: RequestInit): Promise<T> {
  let res: Response;

  try {
    res = await fetch(url, options);
  } catch (error) {
    // This catches browser-level network failures (DNS, Offline, etc.)
    throw new NetworkError(`Unable to connect to server: ${error}`, 'OFFLINE');
  }

  // Handle 401 Unauthorized globally to trigger login redirect
  if (res.status === 401) {
    await handleAuthError(url); // throws AuthRedirectError or redirects
  }

  if (!res.ok) {
    // 1. Handle Proxy/Gateway Errors as NetworkError
    // 502: Bad Gateway (Proxy couldn't reach backend)
    // 503: Service Unavailable (Backend is down/overloaded)
    // 504: Gateway Timeout (Backend took too long)
    if ([502, 503, 504].includes(res.status)) {
      let message = `Service Unavailable (${res.status})`;
      // Try to read the specific error message from your proxy if available
      try {
        const errorBody = await res.json();
        if (errorBody.message) message = errorBody.message;
      } catch { /* ignore */ }
      
      throw new NetworkError(message, res.status === 504 ? 'GATEWAY_TIMEOUT' : 'BAD_GATEWAY');
    }

    // 2. Handle Application Errors (4xx, 500) as ApiError
    let errorMessage = `Server error: ${res.statusText}`;
    let errorData = null;

    try {
      const errorBody = await res.json();
      errorData = errorBody;
      // Adapt this to match your backend's error format
      if (errorBody.detail) {
        errorMessage = typeof errorBody.detail === 'string' 
          ? errorBody.detail 
          : JSON.stringify(errorBody.detail);
      } else if (errorBody.message) {
        errorMessage = errorBody.message;
      }
    } catch { /* ignore parsing error */ }
    
    throw new ApiError(res.status, errorMessage, errorData);
  }

  // 3. Success
  // Handle empty bodies (like 204 No Content) safely
  if (res.status === 204) {
    return {} as T;
  }

  return {
    data: await res.json(),
    status: res.status,
    headers: res.headers,
  } as T;
}
