"use client";
import { sendMessage } from "@/lib/api";
import ChatBar from "../ui/chat_bar";

export default function ChatBarView({ chat_id, user_id }: { chat_id: string, user_id: string }) {
    return (
        <ChatBar onSendMessage={(message) => sendMessage(chat_id, user_id, message)} />
    );
}