import { getMyChatsApiV1UsersMeChatsGet } from "@/lib/api/user/user";
import { UserChatsResponse } from "@/lib/api/model";

export default async function getMyChats() {
    const res = await getMyChatsApiV1UsersMeChatsGet();
    const chats = (res.data as UserChatsResponse).chats || [];
    return chats;
}