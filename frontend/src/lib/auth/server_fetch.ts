"use server";
import { getAccesstToken, injectToken, isRefreshUrl, clearAccessToken, isTokenUrl } from "./session";
import { redirect } from 'next/navigation';
import { stripBaseUrl } from '../utils/utils';

// Entry point into server-side fetch, all requests eventually reach here.
export async function serverFetch(url: string, options: RequestInit): Promise<Response> {
  const isTokenReq = await isRefreshUrl(url) || await isTokenUrl(url);

  // Inject auth headers from cookies securely on the server (if present)
  const accessToken = await getAccesstToken();
  if (accessToken) {
    options = await injectToken(options, accessToken);
  }

  let res =  await fetch(url, options);

  // Handle 401 Unauthorized globally - attempt token refresh if access token is invalid/expired
  if (res.status === 401 && !isTokenReq) {
    console.warn(`Received 401 from serverFetch, redirecting to refresh endpoint ${url}`);

    // This effectively acts like retry trampoline (that catches all 401 errors so they won't invalidate the session until we've had a chance to refresh tokens)
    //    1. we redirect to the refresh endpoint which will attempt to refresh tokens 
    //    2. then redirect back to the original request URL (via next param)
    // Next.js server side components prevent us from setting (deleting) cookies 
    // So reconilliation of session state must be done through redirects (I think, idk if there's a better way to do this)

    // best effort clear (throws an error in server components)
    try {
      await clearAccessToken(); 
    } catch (e) {
      console.warn('Failed to clear access token:', e);
    }

    const urlwithoutBase = stripBaseUrl(url);
    const nextUrl = `/api/auth/refresh?next=/api/proxy${encodeURIComponent(urlwithoutBase)}`; // retry from proxy path
    redirect(nextUrl);
  }

  return res;
}