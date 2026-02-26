import CreateChatButton from "../ui/create_button";

export default function CreateChatButtonComponent({onClick}: {onClick: () => void}) {
    return <CreateChatButton onClick={onClick} />;
}