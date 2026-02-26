"use client";
import { AuthRedirectError } from './errors';

export default async function handleClientAuthError() {
    // Ask server to drop cookie
    await fetch('/logout', { method: 'POST' });
    window.location.href = '/login';
    throw new AuthRedirectError();
}

