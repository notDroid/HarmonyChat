# import pytest
# from harmony.tests.utils import spawn_actor, AppClient

# @pytest.mark.integration
# @pytest.mark.asyncio
# async def test_create_user_flow(app_client: AppClient):
#     # Arrange & Act
#     actor = await spawn_actor(app_client)
#     user_id = actor.user_id

#     # Assert
#     assert isinstance(user_id, str)
#     assert len(user_id) > 0

#     # Verify side effects (e.g., getting chat list should return empty list initially)
#     chats = await actor.get_my_chats()
#     assert chats == []

# @pytest.mark.integration
# @pytest.mark.asyncio
# async def test_delete_user_flow(app_client: AppClient):
#     # Arrange & Act
#     actor = await spawn_actor(app_client)
#     user_id = actor.user_id

#     # Assert
#     assert isinstance(user_id, str)
#     assert len(user_id) > 0

#     # Verify side effects (e.g., getting chat list should return empty list initially)
#     chats = await actor.get_my_chats()
#     assert chats == []

#     # Act - Delete the user
#     await actor.delete_self()

#     # nothing to assert here, just ensure no exceptions and user is effectively deleted