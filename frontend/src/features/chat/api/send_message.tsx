"use server";

import { sendMessageApiV1ChatsChatIdPost } from "@/lib/api/chat/chat";
import { MessageSendRequest } from "@/lib/api/model";

export default async function sendMessage(prevState: any, formData: FormData) {
    const chat_id = formData.get("chat_id") as string;
    const msg: MessageSendRequest = { content: formData.get("content") as string };
    return await sendMessageApiV1ChatsChatIdPost(chat_id, msg);
}