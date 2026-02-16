'use server'

import { redirect } from 'next/navigation'
import { cookies } from 'next/dist/server/request/cookies';

import { loginApiV1AuthTokenPost } from '@/lib/api/auth/auth'
import { BodyLoginApiV1AuthTokenPost } from '@/lib/api/model/bodyLoginApiV1AuthTokenPost';
import { Token } from '@/lib/api/model/token';

import { NetworkError, ApiError } from '@/lib/api/errors';
import { decodeJwt } from 'jose';

export type LoginState = {
  message: string;
}

export async function loginAction(redirectPath: string | null, prevState: any, formData: FormData): Promise<LoginState> {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;

  // Do the login api call
  const loginRequest: BodyLoginApiV1AuthTokenPost = { 
    username: email, 
    password: password,
  };
  
  let res;
  try {
    res = await loginApiV1AuthTokenPost(loginRequest);
  } catch (error) {
    if (error instanceof NetworkError) {
      console.error('Network error:', error);
      return { message: 'Unable to connect. Check your internet.' };
    } 
    
    if (error instanceof ApiError) {
      console.error('API error:', error);
      return { message: error.message || 'Invalid email or password.' };
    } 
    
    console.error('Unexpected error:', error);
    return { message: 'Something went wrong. Please try again.' };
  }
  const token = (res.data as Token).access_token;
  
  // Decode the JWT to get the expiration time (if available) for setting cookie expiration
  const payload = decodeJwt(token);
  const expiresAt = payload.exp ? new Date(payload.exp * 1000) : undefined;

  // Set the Cookie
  const cookieStore = await cookies();
  cookieStore.set('session_token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    expires: expiresAt,
  });

  // Redirect to dashboard
  let destination = '/chats';
  if (redirectPath && redirectPath.startsWith('/') && !redirectPath.startsWith('//')) {
    destination = redirectPath;
  }

  redirect(destination);
}

export async function logoutAction() {
  const cookieStore = await cookies();
  cookieStore.delete('session_token');
  redirect('/login');
}