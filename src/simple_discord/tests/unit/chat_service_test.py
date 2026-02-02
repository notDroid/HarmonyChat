import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from simple_discord.app.schemas import ChatDataItem, ChatMessage
from simple_discord.app.services import ChatService 

# ----------------------------- MOCK DEPENDENCIES ---------------------------- #
@pytest.fixture
def mock_chat_history_repo():
    return AsyncMock()

@pytest.fixture
def mock_user_chat_repo():
    return AsyncMock()

@pytest.fixture
def mock_chat_data_repo():
    return AsyncMock()

@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.return_value.__aenter__.return_value = uow
    uow.commit = AsyncMock()
    return uow

@pytest.fixture
def mock_uow_factory(mock_uow):
    factory = MagicMock()
    factory.return_value = mock_uow
    return factory

@pytest.fixture
def chat_service(mock_chat_history_repo, mock_user_chat_repo, mock_chat_data_repo, mock_uow_factory):
    return ChatService(
        chat_history_repository=mock_chat_history_repo,
        user_chat_repository=mock_user_chat_repo,
        chat_data_repository=mock_chat_data_repo,
        unit_of_work=mock_uow_factory
    )

# -------------------------------- TEST CASES -------------------------------- #
@pytest.mark.asyncio
async def test_create_chat_success(chat_service, mock_chat_data_repo, mock_user_chat_repo):
    """
    Test that providing 2 users creates a chat and calls the repositories.
    """
    # Arrange
    users = ["user1", "user2"]

    # Act
    chat_id = await chat_service.create_chat(users)

    # Assert
    assert isinstance(chat_id, str) # We got a string ID back
    
    # Check that create_chat was called on the data repo
    mock_chat_data_repo.create_chat.assert_called_once()
    
    # Verify the arguments passed to the repo were correct
    # (args[0] is the first positional argument, which is the ChatDataItem)
    called_item = mock_chat_data_repo.create_chat.call_args.args[0]
    assert isinstance(called_item, ChatDataItem)
    assert called_item.chat_id == chat_id

    # Check that the user links were created
    mock_user_chat_repo.create_chat.assert_called_once()


@pytest.mark.asyncio
async def test_create_chat_fails_with_one_user(chat_service, mock_chat_data_repo):
    """
    Test that providing only 1 user raises a ValueError.
    """
    # Arrange
    users = ["user1"]

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        await chat_service.create_chat(users)
    
    assert "at least two users" in str(excinfo.value)
    
    # Crucial: Ensure we did NOT try to save anything to the DB
    mock_chat_data_repo.create_chat.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_success(chat_service, mock_user_chat_repo, mock_chat_history_repo):
    """
    Test sending a message when the user IS a member of the chat.
    """
    # Arrange
    chat_id = "chat_123"
    user_id = "user_ABC"
    content = "Hello world"
    
    mock_user_chat_repo.verify_user_chat.return_value = True

    # Act
    timestamp = await chat_service.send_message(chat_id, user_id, content)

    # Assert
    assert timestamp is not None
    
    # Verify the repository was called to save the message
    mock_chat_history_repo.create_message.assert_called_once()
    saved_msg = mock_chat_history_repo.create_message.call_args.args[0]
    
    assert saved_msg.content == content
    assert saved_msg.user_id == user_id
    assert saved_msg.chat_id == chat_id


@pytest.mark.asyncio
async def test_send_message_permission_denied(chat_service, mock_user_chat_repo, mock_chat_history_repo):
    """
    Test that sending a message fails if the user is NOT a member.
    """
    # Arrange
    # Simulate that verify_user_chat returns False
    mock_user_chat_repo.verify_user_chat.return_value = False

    # Act & Assert
    with pytest.raises(PermissionError) as excinfo:
        await chat_service.send_message("chat_123", "user_intruder", "Hi")

    assert "User is not a member" in str(excinfo.value)
    
    # Ensure we never saved the message
    mock_chat_history_repo.create_message.assert_not_called()


@pytest.mark.asyncio
async def test_get_chat_history(chat_service, mock_chat_history_repo):
    """
    Test retrieving chat history.
    """
    # Arrange
    expected_messages = ["msg1", "msg2"] # Simple fake data
    mock_chat_history_repo.get_chat_history.return_value = expected_messages

    # Act
    result = await chat_service.get_chat_history("chat_123")

    # Assert
    assert result == expected_messages
    mock_chat_history_repo.get_chat_history.assert_called_with("chat_123")