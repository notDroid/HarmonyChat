"use server";
import { clearSession } from '@/lib/auth/session';
import { redirect } from 'next/navigation';

export default async function handleServerAuthError() {
  await clearSession(); // best effort operation
  redirect('/logout');
}