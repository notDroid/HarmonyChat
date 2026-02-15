'use client';

import { useActionState } from 'react';
import { signupAction } from '../actions/signup';
import { SignUpFormUI } from '../ui/signup_form';

const initialSignupState = {
  message: '',
};

export default function SignupPage() {
  const [state, action, isPending] = useActionState(signupAction, initialSignupState);

  return (
    <SignUpFormUI 
      action={action} 
      isPending={isPending} 
      errorMessage={state?.message}
    />
  );
}