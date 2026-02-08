// Thrown when the server responds with a 4xx or 5xx status code
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// Thrown when fetch fails completely (e.g., DNS issue, user offline)
export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}