"use server";

import { sendMessageApiV1ChatsChatIdPost } from "@/lib/api/chat/chat";
import { MessageSendRequest } from "@/lib/api/model";

export type SendMessageState = {
  success?: boolean;
  error?: string;
  data?: any;
} | null;

export default async function sendMessage(
  prevState: SendMessageState, 
  formData: FormData
): Promise<SendMessageState> {
    try {
        const chat_id = formData.get("chat_id") as string;
        const content = formData.get("content") as string;

        if (!chat_id || !content) {
            return { error: "Missing fields" };
        }

        const msg: MessageSendRequest = { content };
        const response = await sendMessageApiV1ChatsChatIdPost(chat_id, msg);
        
        return { success: true, data: response };
    } catch (e) {
        console.error("Failed to send message:", e);
        return { error: "Failed to send message" };
    }
}