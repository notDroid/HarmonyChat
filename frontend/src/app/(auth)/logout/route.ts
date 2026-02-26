import { NextResponse } from 'next/server';
import { clearSession } from '@/features/auth/utils/session';

export async function POST() {
  await clearSession();
  return NextResponse.json({ success: true });
}