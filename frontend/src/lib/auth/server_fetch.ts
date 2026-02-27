"use server";
import { getAccesstToken, injectToken, isRefreshUrl, clearAccessToken } from "./session";
import { redirect } from 'next/navigation';
import { stripBaseUrl } from '../utils/utils';
// Entry point into server-side fetch, all requests eventually reach here.
export async function serverFetch(url: string, options: RequestInit): Promise<Response> {
  const refresh = await isRefreshUrl(url);

  // Inject auth headers from cookies securely on the server (if present)
  const accessToken = await getAccesstToken();
  if (accessToken) {
    options = await injectToken(options, accessToken);
  }

  let res =  await fetch(url, options);

  // Handle 401 Unauthorized globally - attempt token refresh if access token is invalid/expired
  if (res.status === 401 && !refresh) {
    console.warn('Received 401 from serverFetch, redirecting to refresh endpoint');
    // Destroty control flow in order to do this
    // Next.js server side components prevent us from setting (deleting) cookies 
    // So reconilliation of session state must be done through redirects (I think, idk if there's a better way to do this)
    await clearAccessToken(); // best effort clear (doesn't work in server components)
    const urlwithoutBase = stripBaseUrl(url);
    const nextUrl = `/api/auth/refresh?next=/api/proxy/${encodeURIComponent(urlwithoutBase)}`; // retry from proxy path
    redirect(nextUrl);
  }

  return res;
}