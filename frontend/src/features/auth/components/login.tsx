'use client';

import { useActionState } from 'react';
import { useSearchParams } from 'next/navigation';

import { loginAction } from '../actions/login';
import { LoginFormUI } from '../ui/login_form';

const initialLoginState = {
  message: '',
};

export default function LoginPage() {
  const searchParams = useSearchParams();
  const next = searchParams.get('next');
  const loginWithRedirect = loginAction.bind(null, next);
  
  const [state, action, isPending] = useActionState(loginWithRedirect, initialLoginState);


  return (
    <LoginFormUI 
      action={action} 
      isPending={isPending} 
      errorMessage={state?.message}
    />
  );
}