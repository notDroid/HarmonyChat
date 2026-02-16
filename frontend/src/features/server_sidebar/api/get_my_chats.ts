import { getMyChatsApiV1UsersMeChatsGet } from "@/lib/api/user/user";
import { UserChatsResponse } from "@/lib/api/model";

export default async function getMyChats() {
    const res = await getMyChatsApiV1UsersMeChatsGet()
    const chat_id_list = (res.data as UserChatsResponse).chat_id_list || [];
    return chat_id_list;
}