import { getChatHistoryApiV1ChatsChatIdGet } from "@/lib/api/chat/chat";
import { ChatHistoryResponse, ChatMessage } from "@/lib/api/model";

export default async function getChatHistory(chat_id: string): Promise<ChatMessage[]> {
    const res = await getChatHistoryApiV1ChatsChatIdGet(chat_id);
    const data = res.data as ChatHistoryResponse;
    return data.messages;
}