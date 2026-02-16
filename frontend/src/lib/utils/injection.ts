import { getBaseUrl, getAuthHeader, fetchErrorWrapper } from "./utils";

function injectUrl(url: string): string {
  const baseUrl = getBaseUrl();
  return `${baseUrl}${url}`;
}

async function injectAuthHeaders(options: RequestInit): Promise<RequestInit> {
  const headers = new Headers(options.headers);
  const authHeaders = await getAuthHeader();

  if (authHeaders) {
    Object.entries(authHeaders).forEach(([key, value]) => {
      if (value) headers.set(key, value as string);
    });
  }

  const combinedOptions: RequestInit = {
    ...options,
    headers
  };
  return combinedOptions;
}

export const inject = async <T>(
  url: string,
  options: RequestInit
): Promise<T> => {
  
  url = injectUrl(url);
  options = await injectAuthHeaders(options);
  return await fetchErrorWrapper<T>(url, options);
};