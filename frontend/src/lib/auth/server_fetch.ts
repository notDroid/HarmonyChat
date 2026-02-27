"use server";
import { getAccesstToken, getRefreshToken, injectToken, isRefreshUrl } from "./session";
import { refreshAction } from "@/features/auth/actions/refresh";
import { NetworkError } from "../utils/errors";
import { isNextRedirect } from "../utils/errors";

// Entry point into server-side fetch, all requests eventually reach here.
export async function serverFetch(url: string, options: RequestInit): Promise<Response> {
  const refresh = await isRefreshUrl(url);

  // Inject auth headers from cookies securely on the server (if present)
  const accessToken = await getAccesstToken();
  if (accessToken) {
    options = await injectToken(options, accessToken);
  }

  const res =  await fetch(url, options);
  // console.log(`Fetch to ${url} returned status ${res.status}`);

  // // Handle 401 Unauthorized globally - attempt token refresh if access token is invalid/expired
  // if (res.status === 401) {
  //   if (refresh) {
  //     // If we already tried refreshing and still got 401, give up and clear session
  //     return res;
  //   }
  //   console.log(`Attempting to refresh access token due to 401 response from ${url}`);
  //   // Attempt to refresh the access token
  //   try {
  //     await refreshAction();
  //   } catch (error) {
  //     console.log(`Token refresh failed: ${error instanceof Error ? error.message : String(error)}`);
  //     // On 401 this error will propagate up.
  //     if (isNextRedirect(error)) {
  //       throw error;
  //     }

  //     // Treat it like the api call failed due to network (we can retry again)
  //     if (error instanceof NetworkError) {
  //       throw new Error('Network error during token refresh. Please try again.');
  //     }

  //     // Return original 401 response if refresh fails for any other reason (like no refresh token or server error)
  //     return res;
  //   }
  //   console.log(`Refresh successful, retrying original request to ${url}`);
  //   // Retry the original request with the new access token
  //   const newToken = await getAccesstToken();
  //   if (!newToken) {
  //     // If we can't get a new access token, return 401 (should never happen if refresh succeeded, but just in case)
  //     return new Response('Unauthorized', { status: 401 });
  //   }
  //   options = await injectToken(options, newToken);
  //   return await fetch(url, options);
  // }

  return res;
}