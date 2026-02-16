export default function ErrorChatPanel({ message="" }: { message: string }) {
  if (!message) {
    message = "An error occurred while loading the chat. Please try again later.";
  }
  return (
    <div className="flex flex-col items-center justify-center h-full w-full p-4 text-center">
      <h2 className="text-2xl font-bold mb-4">An Error Occurred</h2>
      <p className="mb-4">{message}</p>
      <p className="mb-4">Please try the following steps to resolve the issue:</p>
      <ul className="list-disc list-inside mb-4 text-left">
        <li>Refresh the page.</li>
        <li>Check your internet connection.</li>
        <li>Clear your browser cache and cookies.</li>
        <li>Try using a different browser or device.</li>
      </ul>
      <p>If the problem persists, please contact our support team for further assistance.</p>
    </div>
  );
}