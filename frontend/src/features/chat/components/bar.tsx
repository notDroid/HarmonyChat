"use client";

import { useTransition } from "react";
import sendMessage from "../api/send_message";
import ChatBar from "../ui/bar_form";

export default function ChatBarComponent({ chat_id }: { chat_id: string }) {
    // useTransition allows us to mark the server action as a "transition"
    // providing an isPending state we can pass to the UI.
    const [isPending, startTransition] = useTransition();

    const handleSendMessage = (messageContent: string) => {
        startTransition(async () => {
            // Logic specific to the application:
            // 1. Construct the FormData expected by the Server Action
            const formData = new FormData();
            formData.append("chat_id", chat_id);
            formData.append("content", messageContent);

            // 2. Call the server action
            // We pass 'null' as the first argument because the Server Action 
            // signature expects (prevState, formData) for useActionState compatibility.
            const result = await sendMessage(null, formData);

            // 3. (Optional) Handle errors or logging here
            if (result?.error) {
                console.error(result.error);
                // logic to show toast notification could go here
            }
        });
    };

    return (
        <ChatBar 
            onSendMessage={handleSendMessage} 
            loading={isPending}
        />
    );
}