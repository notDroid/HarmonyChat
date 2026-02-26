import * as Dialog from "@radix-ui/react-dialog";
import { type UseFormReturn } from "react-hook-form";
import { CreateChatFormValues } from "../utils/validation";
import { UserSearchResult } from "../components/create_chat";
import { forwardRef } from "react";

// --- 1. The Dialog Wrapper ---
export const CreateChatDialog = Dialog.Root;

// --- 2. The Trigger Button ---
export const CreateChatTrigger = forwardRef<HTMLButtonElement, Dialog.DialogTriggerProps>(
  ({ className, children, ...props }, ref) => (
    <Dialog.Trigger ref={ref} asChild {...props}>
      <div className="relative group flex items-center justify-center w-full my-1 cursor-pointer">
        <button
          aria-label="Create new chat"
          className="
            h-server-icon w-server-icon
            flex items-center justify-center
            transition-all duration-200 ease-linear
            shadow-sm overflow-hidden
            rounded-[50%] group-hover:rounded-server-icon-expanded
            bg-app-sidebar text-brand group-hover:bg-brand group-hover:text-white
          "
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
        </button>
      </div>
    </Dialog.Trigger>
  )
);
CreateChatTrigger.displayName = "CreateChatTrigger";

// --- 3. The Modal Content ---
interface CreateChatContentProps {
  form: UseFormReturn<CreateChatFormValues>;
  onSubmit: (data: CreateChatFormValues) => void;
  isSubmitting: boolean;
  
  // Search State
  searchValue: string;
  searchResults: UserSearchResult[];
  isSearching: boolean;
  
  // User Management
  onAddUser: (user: UserSearchResult) => void;
  onRemoveUser: (id: string) => void;
  selectedUsers: UserSearchResult[];
  
  // Error State
  rootError: string | null;
}

export const CreateChatContent = ({
  form: { register, handleSubmit, formState: { errors } },
  onSubmit,
  isSubmitting,
  searchValue,
  searchResults,
  isSearching,
  onAddUser,
  onRemoveUser,
  selectedUsers,
  rootError
}: CreateChatContentProps) => {
  return (
    <Dialog.Portal>
      {/* Backdrop */}
      <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
      
      {/* Modal Content */}
      <Dialog.Content className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-md translate-x-[-50%] translate-y-[-50%] border border-app-outline bg-app-bg shadow-xl duration-200 sm:rounded-xl overflow-hidden max-h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-app-outline bg-app-sidebar px-6 py-4 shrink-0">
          <Dialog.Title className="text-lg font-semibold text-app-text">Create New Chat</Dialog.Title>
          <Dialog.Close className="text-app-muted hover:text-app-text transition-colors rounded-sm focus:outline-none focus:ring-2 focus:ring-brand">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Dialog.Close>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6 p-6 overflow-y-auto">
          
          {/* API Error Alert */}
          {rootError && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 text-sm text-red-600 dark:text-red-400">
              <p className="font-medium">Error creating chat</p>
              <p>{rootError}</p>
            </div>
          )}

          {/* Metadata Section */}
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1">
              <input
                {...register("title")}
                placeholder="Chat Title"
                className="w-full rounded-md border border-app-outline bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all"
              />
              {errors.title && <span className="text-xs text-red-500">{errors.title.message}</span>}
            </div>
            
            <div className="flex flex-col gap-1">
              <input
                {...register("description")}
                placeholder="Description (Optional)"
                className="w-full rounded-md border border-app-outline bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all"
              />
              {errors.description && <span className="text-xs text-red-500">{errors.description.message}</span>}
            </div>
          </div>

          <div className="h-px bg-app-outline w-full" />

          {/* Member Selection Section */}
          <div className="flex flex-col gap-3">
            <label className="text-sm font-medium text-app-text">
              Add Members <span className="text-app-muted font-normal ml-1">({selectedUsers.length}/10)</span>
            </label>

            {/* Selected Users Pills */}
            {selectedUsers.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-1">
                {selectedUsers.map((u) => (
                  <div key={u.user_id} className="flex items-center gap-1.5 bg-brand/10 text-brand px-2.5 py-1 rounded-full text-xs font-medium border border-brand/20">
                    <span>{u.username}</span>
                    <button 
                      type="button" 
                      onClick={() => onRemoveUser(u.user_id)} 
                      className="hover:text-red-600 focus:outline-none"
                    >
                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 6L6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            {/* Search Input */}
            <div className="relative">
              <input
                {...register("search")}
                autoComplete="off"
                placeholder="Search by email..."
                className="w-full rounded-md border border-app-outline bg-app-sidebar px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all"
              />
              
              {/* Results List - Now Block/Relative (Not Absolute) to avoid clipping */}
              {searchValue && (
                <div className="mt-2 w-full border border-app-outline rounded-md bg-app-sidebar shadow-sm overflow-hidden animate-in fade-in slide-in-from-top-1">
                  {isSearching ? (
                    <div className="p-4 text-center text-xs text-app-muted animate-pulse">Searching...</div>
                  ) : searchResults.length > 0 ? (
                    <ul className="divide-y divide-app-outline/50 max-h-40 overflow-y-auto">
                      {searchResults.map((user) => (
                        <li key={user.user_id}>
                          <button
                            type="button" // Important: prevents form submission on click
                            onClick={() => onAddUser(user)}
                            className="w-full text-left p-3 hover:bg-app-hover transition-colors flex flex-col gap-0.5"
                          >
                            <span className="text-sm font-medium text-app-text">{user.username}</span>
                            <span className="text-xs text-app-muted">{user.email}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="p-4 text-center text-xs text-app-muted">No users found</div>
                  )}
                </div>
              )}
            </div>
            
            {errors.user_id_list && <span className="text-xs text-red-500">{errors.user_id_list.message}</span>}
          </div>

          {/* Footer Actions */}
          <div className="pt-2 mt-auto">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>
                  Creating...
                </span>
              ) : (
                "Create Chat"
              )}
            </button>
          </div>
        </form>
      </Dialog.Content>
    </Dialog.Portal>
  );
};