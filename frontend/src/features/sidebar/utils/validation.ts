import { z } from "zod";

export const createChatSchema = z.object({
  title: z.string().min(1, "Title is required").max(100, "Title must be less than 100 characters"),
  description: z.string().max(500, "Description must be less than 500 characters").optional(),
  search: z.string().optional(),
  user_id_list: z.array(z.string()).max(10, "You can only add up to 10 users."),
});

export type CreateChatFormValues = z.infer<typeof createChatSchema>;