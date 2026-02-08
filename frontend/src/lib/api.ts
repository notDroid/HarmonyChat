import { ApiError, NetworkError } from "./errors";

const host_name = "walis-macbook-pro";
const API_ENDPOINT = `http://${host_name}:8000/api/v1/`;

async function secure_fetch(url: string, options?: RequestInit) {
  let res: Response;

  try {
    res = await fetch(url, options);
  } catch (error) {
    // If fetch throws, it's a network issue (DNS, Offline, etc.)
    throw new NetworkError('Unable to connect to server');
  }

  // Handle API Errors (404, 500, 401, etc.)
  if (!res.ok) {
    throw new ApiError(res.status, `Server error: ${res.statusText}`);
  }

  // Can throw a syntax error, which should crash the website 
  // since if it happens it indicates a serious issue with the API response.
  return await res.json();
}

export async function getChatHistory(chat_id: string, user_id: string) {
  const res = await secure_fetch(`${API_ENDPOINT}chats/${chat_id}?user_id=${user_id}`);
  return res;
}

export async function sendMessage(chat_id: string, user_id: string, content: string) {
  const res = await secure_fetch(`${API_ENDPOINT}chats/${chat_id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id, content }),
  });
  return res;
}
