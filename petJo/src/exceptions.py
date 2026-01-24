"""Custom exceptions for the PetJo API."""


class PetJoException(Exception):
    """Base exception for PetJo application."""
    
    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(PetJoException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found",
            status_code=404
        )


class PetNotFoundException(NotFoundException):
    """Exception raised when a pet is not found."""
    
    def __init__(self):
        super().__init__(resource="Pet")


class UserNotFoundException(NotFoundException):
    """Exception raised when a user is not found."""
    
    def __init__(self):
        super().__init__(resource="User")


class ProfileNotFoundException(NotFoundException):
    """Exception raised when a profile is not found."""
    
    def __init__(self):
        super().__init__(resource="Profile")


class UnauthorizedException(PetJoException):
    """Exception raised when user is not authorized."""
    
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message=message, status_code=403)


class AuthenticationException(PetJoException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class InvalidCredentialsException(AuthenticationException):
    """Exception raised when credentials are invalid."""
    
    def __init__(self):
        super().__init__(message="Invalid email or password")


class ValidationException(PetJoException):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=400)


class DuplicateException(PetJoException):
    """Exception raised when trying to create a duplicate resource."""
    
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} already exists",
            status_code=409
        )


class EmailAlreadyExistsException(DuplicateException):
    """Exception raised when email is already registered."""
    
    def __init__(self):
        super().__init__(resource="Email")


class InactiveAccountException(AuthenticationException):
    """Exception raised when account is inactive."""
    
    def __init__(self):
        super().__init__(message="Account is inactive")


class PermissionDeniedException(UnauthorizedException):
    """Exception raised when user doesn't have required permissions."""
    
    def __init__(self, action: str = "perform this action"):
        super().__init__(message=f"You don't have permission to {action}")


class SuperAdminRequiredException(UnauthorizedException):
    """Exception raised when super admin access is required."""
    
    def __init__(self):
        super().__init__(message="Super admin access required")


class ForbiddenException(UnauthorizedException):
    """Exception raised when access to resource is forbidden."""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message=message)
