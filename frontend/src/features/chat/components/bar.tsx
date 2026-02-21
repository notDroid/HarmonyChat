"use client";
import ChatBar from "./bar_form";
import useSendMessage from "../api/use_send_message";

export default function ChatBarComponent({ chat_id }: { chat_id: string }) {
    const { mutate: send, isPending } = useSendMessage(chat_id);

    const handleSendMessage = (messageContent: string) => {
        const client_uuid = crypto.randomUUID();
        send({ content: messageContent, client_uuid });
    };

    return (
        <ChatBar 
            onSendMessage={handleSendMessage} 
            loading={isPending}
        />
    );
}