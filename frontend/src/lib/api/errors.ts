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

// Custom error to signal that we need to redirect to login
// We need to be careful to catch this on the client side and not treat it as a generic error
export class AuthRedirectError extends Error {
  constructor() {
    super('Redirecting to login...');
    this.name = 'AuthRedirectError';
  }
}