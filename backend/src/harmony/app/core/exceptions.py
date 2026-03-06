

class HarmonyError(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NotFoundError(HarmonyError):
    """Raised when a requested resource (User, Chat, etc.) does not exist."""
    pass

class AuthorizationError(HarmonyError):
    """Raised when a user does not have permission to perform an action."""
    pass

class AuthenticationError(HarmonyError):
    """Raised when credentials are invalid or missing."""
    pass

class ConflictError(HarmonyError):
    """Raised when an operation violates database constraints or business rules."""
    pass

class ValidationError(HarmonyError):
    """Raised when input data is semantically invalid."""
    pass