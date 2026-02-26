"use server";

import { createChatApiV1ChatsPost } from "@/lib/api/chat/chat";
import { ChatCreateRequest, ChatResponse } from "@/lib/api/model";

export async function createChatAction(chatCreateRequest: ChatCreateRequest): Promise<ChatResponse> {
    const res = await createChatApiV1ChatsPost(chatCreateRequest);
    return res.data as ChatResponse;
}