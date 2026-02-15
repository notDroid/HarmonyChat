// import ServerSidebarComponent from "../components/client_server_sidebar";
// import { getChatList } from "@/lib/api";
// import { getUserId } from "@/lib/utils";

export default async function ServerSidebarView() {
    // For now, just return a placeholder sidebar. We can implement the actual server list later.
    return <div className="w-20 bg-gray-800 h-screen shrink-0" />;
    // const user_id = await getUserId();
    // const chat_id_list: string[] = await getChatList(user_id).then(res => res.chat_id_list);
    // return (
    //     <ServerSidebarComponent chat_id_list={chat_id_list} />
    // );
}