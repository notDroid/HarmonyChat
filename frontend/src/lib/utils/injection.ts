import { getBaseUrl, fetchErrorWrapper } from "./utils";

function injectUrl(url: string): string {
  const baseUrl = getBaseUrl();
  return `${baseUrl}${url}`;
}

export const inject = async <T>(
  url: string,
  options: RequestInit
): Promise<T> => {
  url = injectUrl(url);
  return await fetchErrorWrapper<T>(url, options);
};