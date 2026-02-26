import { SyntheticEvent } from "react";
import { UserSearchResult } from "../components/create_chat_form";

interface CreateChatModalUIProps {
  isOpen: boolean;
  onClose: () => void;
  
  // Form values
  title: string;
  setTitle: (val: string) => void;
  description: string;
  setDescription: (val: string) => void;
  searchInput: string;
  setSearchInput: (val: string) => void;
  
  // User selection
  selectedUsers: UserSearchResult[];
  onAddUser: (user: UserSearchResult) => void;
  onRemoveUser: (userId: string) => void;
  
  // Submission & Data
  onSubmit: (e: SyntheticEvent) => void;
  searchResults: UserSearchResult[];
  isSearching: boolean;
  isSubmitting: boolean;
  isValid: boolean;
}

export default function CreateChatModalUI({
  isOpen, onClose,
  title, setTitle, description, setDescription,
  searchInput, setSearchInput, selectedUsers,
  onAddUser, onRemoveUser, onSubmit,
  searchResults, isSearching, isSubmitting, isValid
}: CreateChatModalUIProps) {
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm transition-opacity p-4">
      {/* Click outside to close */}
      <div className="absolute inset-0" onClick={onClose} aria-hidden="true" />
      
      {/* Modal Container */}
      <div className="relative w-full max-w-md max-h-[90vh] flex flex-col rounded-xl border border-app-outline bg-app-bg shadow-xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-app-outline bg-app-sidebar shrink-0">
          <h2 className="text-lg font-semibold text-app-text">Create New Chat</h2>
          <button onClick={onClose} className="text-app-muted hover:text-app-text transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={onSubmit} className="flex flex-col flex-1 overflow-y-auto p-5 space-y-5">
          
          {/* Metadata Inputs */}
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Chat Title (Optional)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={100}
              className="w-full rounded-md border border-app-outline bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand focus:outline-none"
            />
            <input
              type="text"
              placeholder="Description (Optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              className="w-full rounded-md border border-app-outline bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand focus:outline-none"
            />
          </div>

          <hr className="border-app-outline" />

          {/* User Selection Area */}
          <div className="space-y-3 flex-1 flex flex-col min-h-0">
            <label className="text-sm font-medium text-app-text">
              Add Members <span className="text-app-muted font-normal">({selectedUsers.length}/10)</span>
            </label>
            
            {/* Selected Users Pills */}
            {selectedUsers.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedUsers.map(user => (
                  <div key={user.user_id} className="flex items-center gap-1.5 bg-brand/10 text-brand px-2.5 py-1 rounded-full text-xs font-medium border border-brand/20">
                    <span>{user.username}</span>
                    <button type="button" onClick={() => onRemoveUser(user.user_id)} className="hover:text-red-500">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Search Input */}
            <input
              type="text"
              placeholder="Search by username or email..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full rounded-md border border-app-outline bg-app-sidebar px-3 py-2 text-sm text-app-text placeholder:text-app-muted focus:border-brand focus:ring-1 focus:ring-brand focus:outline-none"
            />

            {/* Search Results Dropdown/List */}
            {searchInput.length > 0 && (
              <div className="flex-1 overflow-y-auto border border-app-outline rounded-md bg-app-sidebar min-h-[120px]">
                {isSearching ? (
                  <div className="p-3 text-center text-sm text-app-muted animate-pulse">Searching...</div>
                ) : searchResults.length > 0 ? (
                  <ul className="divide-y divide-app-outline">
                    {searchResults.map(user => (
                      <li 
                        key={user.user_id}
                        onClick={() => onAddUser(user)}
                        className="p-2.5 hover:bg-app-hover cursor-pointer transition-colors flex flex-col"
                      >
                        <span className="text-sm font-medium text-app-text">{user.username}</span>
                        <span className="text-xs text-app-muted">{user.email}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="p-3 text-center text-sm text-app-muted">No users found.</div>
                )}
              </div>
            )}
          </div>
          
          {/* Submit Button */}
          <button
            type="submit"
            disabled={!isValid || isSubmitting}
            className="w-full mt-auto rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-50 disabled:cursor-not-allowed transition-opacity shrink-0"
          >
            {isSubmitting ? "Creating..." : "Create Chat"}
          </button>
        </form>
      </div>
    </div>
  );
}