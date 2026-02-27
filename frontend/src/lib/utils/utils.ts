import { ApiError, NetworkError, isNextRedirect } from './errors';
import handleServerAuthError from './server_auth_error';
import handleClientAuthError from './client_auth_error';
import { serverFetch } from '../auth/server_fetch';

const isServer = typeof window === 'undefined';

export const getBaseUrl = () => {
  if (isServer) {
    return process.env.INTERNAL_API_ENDPOINT; 
  } else {
    return '/api/proxy'; 
  }
};

export const stripBaseUrl = (url: string) => {
  let urlwithoutBase = url.replace(process.env.INTERNAL_API_ENDPOINT || '', '');
  urlwithoutBase = urlwithoutBase.replace(process.env.NEXT_PUBLIC_INTERNAL_API_ENDPOINT || '', '');
  return urlwithoutBase;
};

export async function fetchErrorWrapper<T>(url: string, options?: RequestInit): Promise<T> {
  let res: Response;

  try {
    if (isServer) {
      res = await serverFetch(url, options || {});
    } else {
      res = await fetch(url, options);
    }
  } catch (error) {
    if (isNextRedirect(error)) {
      // Careful to let this happen when refresh token api call returns 401
      throw error; 
    }
    // This catches browser-level network failures (DNS, Offline, etc.)
    throw new NetworkError(`Unable to connect to server: ${error}`, 'OFFLINE');
  }

  // Handle 401 Unauthorized globally to trigger login redirect
  if (res.status === 401) {
    // Eventually reaches clearSession()
    if (isServer) {
      await handleServerAuthError();
    } else {
      handleClientAuthError();
    }
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
