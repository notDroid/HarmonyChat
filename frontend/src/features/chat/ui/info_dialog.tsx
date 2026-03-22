import * as Dialog from "@radix-ui/react-dialog";
import { forwardRef } from "react";

export const ChatInfoDialog = Dialog.Root;

export const ChatInfoTrigger = forwardRef<HTMLButtonElement, Dialog.DialogTriggerProps>(
    ({ className, ...props }, ref) => (
        <Dialog.Trigger ref={ref} asChild {...props}>
            <button
                aria-label="Chat Information"
                className="p-2 text-app-muted hover:text-app-text hover:bg-app-hover transition-colors rounded-md focus:outline-none focus:ring-2 focus:ring-brand"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                </svg>
            </button>
        </Dialog.Trigger>
    )
);
ChatInfoTrigger.displayName = "ChatInfoTrigger";

interface ChatInfoContentProps {
    onDelete: () => void;
    isDeleting: boolean;
    onLeave: () => void;
    isLeaving: boolean;
}

export const ChatInfoContent = ({ onDelete, isDeleting, onLeave, isLeaving }: ChatInfoContentProps) => {
    return (
        <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
            <Dialog.Content className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-md translate-x-[-50%] translate-y-[-50%] border border-app-outline bg-app-bg shadow-xl duration-200 sm:rounded-xl overflow-hidden">
                
                <div className="flex items-center justify-between border-b border-app-outline bg-app-sidebar px-6 py-4">
                    <Dialog.Title className="text-lg font-semibold text-app-text">Chat Information</Dialog.Title>
                    <Dialog.Close className="text-app-muted hover:text-app-text transition-colors rounded-sm focus:outline-none">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </Dialog.Close>
                </div>

                <div className="p-6 space-y-6">
                    <div className="text-sm text-app-muted">
                        More settings and participant lists will go here.
                    </div>
                    
                    <div className="h-px bg-app-outline w-full" />
                    
                    <div className="space-y-3">
                        <h3 className="text-sm font-semibold text-app-error">Danger Zone</h3>
                        
                        <button
                            onClick={onLeave}
                            disabled={isLeaving}
                            className="w-full flex justify-between items-center px-4 py-2.5 rounded-md border border-app-error/50 text-app-error bg-app-error/5 hover:bg-app-error/10 disabled:opacity-50 transition-colors text-sm font-medium"
                        >
                            {isLeaving ? "Leaving..." : "Leave Chat"}
                            {!isLeaving && (
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                                </svg>
                            )}
                        </button>

                        <button
                            onClick={onDelete}
                            disabled={isDeleting}
                            className="w-full flex justify-between items-center px-4 py-2.5 rounded-md border border-app-error/50 text-app-error bg-app-error/5 hover:bg-app-error/10 disabled:opacity-50 transition-colors text-sm font-medium"
                        >
                            {isDeleting ? "Deleting..." : "Delete Chat"}
                            {!isDeleting && (
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>

            </Dialog.Content>
        </Dialog.Portal>
    );
};