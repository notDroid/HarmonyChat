import Link from 'next/link';

interface SignUpFormUIProps {
  action: (payload: FormData) => void;
  isPending: boolean;
  errorMessage?: string;
}

export function SignUpFormUI({ action, isPending, errorMessage }: SignUpFormUIProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-app-bg p-4 transition-colors duration-200">
      <div className="w-full max-w-md rounded-2xl border border-app-outline bg-app-sidebar p-8 shadow-sm">
        
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-app-text">
            Create an account
          </h1>
          <p className="mt-2 text-sm text-app-muted">
            Get started with your new dashboard
          </p>
        </div>

        {/* Form */}
        <form action={action} className="space-y-6">
          
          {/* Username Input */}
          <div className="space-y-2">
            <label 
              htmlFor="username" 
              className="text-sm font-medium leading-none text-app-text"
            >
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              placeholder="johndoe"
              required
              disabled={isPending}
              className="w-full rounded-md border border-app-outline bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand focus:outline-none disabled:opacity-50"
            />
          </div>

          {/* Email Input */}
          <div className="space-y-2">
            <label 
              htmlFor="email" 
              className="text-sm font-medium leading-none text-app-text"
            >
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              placeholder="name@example.com"
              required
              disabled={isPending}
              className="w-full rounded-md border border-app-outline bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand focus:outline-none disabled:opacity-50"
            />
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <label 
              htmlFor="password" 
              className="text-sm font-medium leading-none text-app-text"
            >
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              disabled={isPending}
              className="w-full rounded-md border border-app-outline bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand focus:outline-none disabled:opacity-50"
            />
          </div>

          {/* Error Message Alert */}
          {errorMessage && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
              {errorMessage}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isPending}
            className="w-full rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {isPending ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Creating account...
              </span>
            ) : (
              'Sign up'
            )}
          </button>
        </form>

        {/* Link to Login */}
        <div className="mt-6 text-center text-sm">
          <span className="text-app-muted">Already have an account? </span>
          <Link 
            href="/login" 
            className="font-medium text-brand hover:underline"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}