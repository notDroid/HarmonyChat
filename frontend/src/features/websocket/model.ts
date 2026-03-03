import { ChatMessage } from '@/lib/api/model';

export type ChatEvent = 
  | { type: 'chat_message'; payload: ChatMessage }
  | { type: 'user_joined'; payload: { chat_id: string; user_id: string } }
  | { type: 'chat_deleted'; payload: { chat_id: string } };