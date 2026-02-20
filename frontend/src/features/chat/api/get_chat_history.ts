import { getChatHistoryApiV1ChatsChatIdGet } from "@/lib/api/chat/chat";
import { ChatHistoryResponse } from "@/lib/api/model";

export default async function getChatHistory(chat_id: string, limit?: number, cursor?: string): Promise<ChatHistoryResponse> {
    const params: any = {};
    if (limit !== undefined) params.limit = limit;
    if (cursor !== undefined) params.cursor = cursor;

    const res = await getChatHistoryApiV1ChatsChatIdGet(chat_id, params);
    const data = res.data as ChatHistoryResponse;
    return data;
}