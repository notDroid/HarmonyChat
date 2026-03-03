"use client";
import ChatBar from "./bar_form";
import useSendMessage from "../api/use_send_message";
import { v4 as uuidv4 } from 'uuid';

export default function ChatBarComponent({ chat_id }: { chat_id: string }) {
    const { mutate: send, isPending } = useSendMessage(chat_id);

    const handleSendMessage = (messageContent: string) => {
        const client_uuid = uuidv4();
        send({ content: messageContent, client_uuid });
    };

    return (
        <ChatBar 
            onSendMessage={handleSendMessage} 
            loading={isPending}
        />
    );
}