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