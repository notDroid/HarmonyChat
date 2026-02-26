"use server";
import { createChatApiV1ChatsPost } from "@/lib/api/chat/chat";
import { ChatCreateRequest, ChatResponse } from "@/lib/api/model";

async function createChat(chatCreateRequest: ChatCreateRequest) {
    const res = await createChatApiV1ChatsPost(chatCreateRequest);
    return res.data;
}

export async function createChatAction(prevState: any, formData: FormData): Promise<ChatResponse> {
    const chatCreateRequest: ChatCreateRequest = {
        title: formData.get("name") as string,
        description: formData.get("description") as string,
        user_id_list: (formData.get("user_ids") as string).split(",").map(id => id.trim()),
    };
    return await createChat(chatCreateRequest) as ChatResponse;
}