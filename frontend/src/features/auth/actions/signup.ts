'use server'

import { redirect } from 'next/navigation'
import { signUpApiV1UsersPost } from '@/lib/api/user/user'
import { UserCreateRequest } from '@/lib/api/model/'
import { NetworkError, ApiError } from '@/lib/api/errors';

export type SignupState = {
  message: string;
}

export async function signupAction(prevState: any, formData: FormData): Promise<SignupState> {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;
  const username = formData.get('username') as string;

  const signUpRequest: UserCreateRequest = {
    email: email,
    password: password,
    username: username,
  };

  try {
    await signUpApiV1UsersPost(signUpRequest);
  } catch (error) {
    if (error instanceof NetworkError) {
      return { message: 'Unable to connect. Check your internet.' };
    } 
    
    if (error instanceof ApiError) {
      return { message: error.message || 'Unable to create account.' };
    } 
    
    return { message: 'Something went wrong. Please try again.' };
  }

  // Redirect to login on success
  redirect('/login');
}