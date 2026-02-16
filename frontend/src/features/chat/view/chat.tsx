// // Views
// import ChatHeaderView from "./chat_header";
// import ChatPanelView from "../components/chat_panel";
// import ChatBarView from "../components/chat_bar";

// // UI Components
// import ErrorChatPanel from "../ui/chat_error_panel";

// // API Functions
// import { getChatHistory} from "@/lib/api";
// import { ApiError, NetworkError } from "@/lib/api/errors";

// // Temporary constants for demo purposes.
// const refreshInterval = 1000;
// const user_id ='01KGX14KWXN0TR47C3N36N7ZBN';


// export default async function ChatWindowView({ chat_id }: { chat_id: string }) {
//   let initial_messages = [];
//   let loaded = false;

//   try {
//     // await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate loading delay
//     initial_messages = await getChatHistory(chat_id, user_id);
//     loaded = true;
  
//   } catch (error) {

//     console.log("Failed to fetch initial chat history:", error);
//     // Throw the error page on API errors, for network errors fall back to the loading page.
//     if (error instanceof ApiError) {
//       return <ErrorChatPanel message={`${error.message}`} />;
//     } else if (!(error instanceof NetworkError)) {
//       throw error;
//     }

//   }

//   return (
//     <div className="flex h-full w-full flex-col min-w-0">
//       <ChatHeaderView />
//       <ChatPanelView chat_id={chat_id} user_id={user_id} refreshInterval={refreshInterval} initial_messages={initial_messages} loaded={loaded} />
//       <ChatBarView chat_id={chat_id} user_id={user_id} />
//     </div>
//   );
// }