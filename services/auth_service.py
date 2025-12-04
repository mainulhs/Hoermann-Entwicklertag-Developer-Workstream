"""
Authentication Service for Industrial Monitoring System
Handles user authentication and session management

SECURITY VULNERABILITIES (INTENTIONAL):
- Weak random token generation using predictable random.randint()
- No token expiration
"""

import random
from typing import Dict, Optional
from repositories.users import UserRepository


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class Result:
    """Result object for service operations"""
    
    def __init__(self, success: bool, data: Optional[Dict] = None, error_message: Optional[str] = None):
        self.success = success
        self.data = data
        self.error_message = error_message
        self.token = data.get('token') if data else None


class AuthService:
    """
    Business logic for authentication and session management
    
    INTENTIONAL FLAWS:
    - Weak token generation using predictable random numbers
    - No token expiration mechanism
    """
    
    def __init__(self, user_repo: UserRepository):
        """
        Initialize AuthService
        
        Args:
            user_repo: UserRepository instance for user data access
        """
        self.user_repo = user_repo
        # In-memory token storage (not suitable for production)
        self.token_store: Dict[str, Dict] = {}
    
    def generate_token(self, username: str) -> str:
        """
        Generate authentication token for user
        
        INTENTIONAL SECURITY VULNERABILITY: Weak token generation
        Uses predictable random.randint() instead of cryptographically secure
        random number generation (e.g., secrets.token_urlsafe()).
        
        Args:
            username: Username to generate token for
            
        Returns:
            Authentication token (INSECURE!)
        """
        # INSECURE CODE - DO NOT USE IN PRODUCTION
        # Using predictable random number generation
        token = f"{username}_{random.randint(1000, 9999)}"
        return token
    
    def login(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate user and generate session token
        
        INTENTIONAL SECURITY FLAW: No token expiration
        Tokens never expire, allowing indefinite access.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authentication token if successful, None if authentication fails
        """
        # Authenticate user
        user = self.user_repo.authenticate(username, password)
        
        if not user:
            return None
        
        # Generate token (using weak generation)
        token = self.generate_token(username)
        
        # Store token with user info (no expiration - INSECURE!)
        self.token_store[token] = {
            'username': username,
            'user_id': user['id'],
            'role': user['role']
            # INTENTIONAL FLAW: No 'expires_at' field
        }
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate authentication token
        
        INTENTIONAL SECURITY FLAW: No token expiration check
        Tokens are valid forever once created.
        
        Args:
            token: Authentication token to validate
            
        Returns:
            User information dictionary if token is valid, None otherwise
        """
        # INSECURE CODE - DO NOT USE IN PRODUCTION
        # No expiration check - tokens never expire!
        return self.token_store.get(token)
    
    def create_user(self, username: str, password: str, role: str = 'operator') -> Result:
        """
        Create a new user account
        
        Args:
            username: Unique username
            password: User password
            role: User role (operator, technician, manager, admin)
            
        Returns:
            Result object with success status
        """
        try:
            # Validate username
            if not username or not isinstance(username, str):
                return Result(
                    success=False,
                    error_message="Username must be a non-empty string"
                )
            
            # Validate password
            if not password or not isinstance(password, str):
                return Result(
                    success=False,
                    error_message="Password must be a non-empty string"
                )
            
            # Check if username already exists
            existing_user = self.user_repo.get_by_username(username)
            if existing_user:
                return Result(
                    success=False,
                    error_message=f"Username '{username}' already exists"
                )
            
            # Create user
            user_id = self.user_repo.create(username, password, role)
            
            return Result(
                success=True,
                data={
                    'user_id': user_id,
                    'username': username,
                    'role': role
                }
            )
            
        except Exception as e:
            return Result(
                success=False,
                error_message=f"Failed to create user: {str(e)}"
            )
    
    def logout(self, token: str) -> bool:
        """
        Logout user by invalidating token
        
        Args:
            token: Authentication token to invalidate
            
        Returns:
            True if logout successful, False if token not found
        """
        if token in self.token_store:
            del self.token_store[token]
            return True
        return False
    
    def get_user_info(self, token: str) -> Optional[Dict]:
        """
        Get user information from token
        
        Args:
            token: Authentication token
            
        Returns:
            User information dictionary or None if token invalid
        """
        return self.validate_token(token)
    
    def require_auth(self, token: Optional[str]) -> Dict:
        """
        Require valid authentication token
        
        Args:
            token: Authentication token to validate
            
        Returns:
            User information dictionary
            
        Raises:
            AuthenticationError: If token is missing or invalid
        """
        if not token:
            raise AuthenticationError("Authentication token required")
        
        user_info = self.validate_token(token)
        if not user_info:
            raise AuthenticationError("Invalid or expired authentication token")
        
        return user_info
