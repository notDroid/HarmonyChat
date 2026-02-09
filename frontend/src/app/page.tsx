import AuthWrapper from '@/features/auth/auth_wrapper';

export default function DashboardPage() {
  return (
    <AuthWrapper>
      {/* This content is only visible to logged-in users */}
      <div className="bg-gray-100 p-4 rounded">
        <h2>Protected Dashboard Content</h2>
        <p>If you can see this, you are authenticated!</p>
      </div>
    </AuthWrapper>
  );
}

