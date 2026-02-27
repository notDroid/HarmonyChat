"use client";
import { AuthRedirectError } from './errors';

export default async function handleClientAuthError() {
  console.warn('Handling client auth error, clearing session and redirecting to login');
  // Ask server to drop cookie
  await fetch('/logout', { method: 'POST' });
  window.location.href = '/login';
  throw new AuthRedirectError();
}