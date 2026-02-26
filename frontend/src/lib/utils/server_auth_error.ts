"use server";
import { clearSession } from '@/features/auth/utils/session';
import { redirect } from 'next/navigation';

export default async function handleServerAuthError() {
  // clear session and redirect to login
  await clearSession();
  redirect('/login');
}