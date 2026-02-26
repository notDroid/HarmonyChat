import { isRedirectError } from "next/dist/client/components/redirect-error";

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string, public code: 'OFFLINE' | 'GATEWAY_TIMEOUT' | 'BAD_GATEWAY' = 'OFFLINE') {
    super(message);
    this.name = 'NetworkError';
  }
}

// thrown on the client when we detect a 401 response, to trigger the auth error handling flow
export class AuthRedirectError extends Error {
  constructor() {
    super('Redirecting to login...');
    this.name = 'AuthRedirectError';
  }
}

// Utility function to detect if an error is a Next.js redirect (used in server components)
export function isNextRedirect(error: unknown) {
  return isRedirectError(error);
}