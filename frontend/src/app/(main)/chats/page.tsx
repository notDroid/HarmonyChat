export default async function HomePage() {
  // do a timeout to simulate loading
  // await new Promise((resolve) => setTimeout(resolve, 1000));
  return (
    <div className="flex items-center justify-center h-screen">
      <h1 className="text-2xl font-bold">Welcome to Harmony!</h1>
    </div>
  );
}