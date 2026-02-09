'use client';

import { Authenticator, useTheme, View, Image, Text, Heading } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_USER_POOL_ID!,
      userPoolClientId: process.env.NEXT_PUBLIC_USER_POOL_CLIENT_ID!,
    }
  }
});

// 1. Define custom components for the "slots"
const components = {
  Header() {
    return (
      <View textAlign="center" padding="large">
        <Heading level={3}>Harmony Chat</Heading>
        <Text color="gray">Sign in to continue</Text>
      </View>
    );
  },
};

export default function AuthWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-50">
      <Authenticator 
        components={components}
      >
        {({ signOut, user }) => (
          <main className="w-full min-h-screen p-8 bg-white">
            <div className="max-w-4xl mx-auto">
              <div className="flex justify-between items-center mb-8">
                <h1 className="text-2xl font-bold">Hello, {user?.username}</h1>
                <button 
                  onClick={signOut}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                >
                  Sign out
                </button>
              </div>
              
              <div className="mt-8">
                {children}
              </div>
            </div>
          </main>
        )}
      </Authenticator>
    </div>
  );
}