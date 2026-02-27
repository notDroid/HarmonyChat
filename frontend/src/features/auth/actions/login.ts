'use server'

import { redirect } from 'next/navigation'

import { loginApiV1AuthTokenPost } from '@/lib/api/auth/auth'
import { BodyLoginApiV1AuthTokenPost } from '@/lib/api/model/bodyLoginApiV1AuthTokenPost';
import { Token } from '@/lib/api/model/token';

import { NetworkError, ApiError, isNextRedirect } from '@/lib/utils/errors';
import { setToken } from '@/lib/auth/session';

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
    if (isNextRedirect(error)) throw error;
    
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

  // Set tokens
  const tokens = (res.data as Token[]);
  for (const token of tokens) {
    await setToken(token);
  }

  // Redirect to dashboard
  let destination = '/chats';
  if (redirectPath && redirectPath.startsWith('/') && !redirectPath.startsWith('//')) {
    destination = redirectPath;
  }

  redirect(destination);
}