"""
User Repository for Industrial Monitoring System
Handles user creation and authentication

SECURITY VULNERABILITY (INTENTIONAL):
- Passwords stored in plain text (no hashing)
"""

from typing import Optional, Dict
from database import DatabaseManager


class UserRepository:
    """
    Repository for user data access operations
    
    INTENTIONAL FLAW: Plain text password storage
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize UserRepository
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def create(self, username: str, password: str, role: str = 'operator') -> int:
        """
        Create a new user account
        
        INTENTIONAL SECURITY VULNERABILITY: Plain text password storage
        Passwords should be hashed using bcrypt, argon2, or similar before storage.
        
        Args:
            username: Unique username
            password: User password (stored in plain text - INSECURE!)
            role: User role (operator, technician, manager, admin)
        
        Returns:
            ID of the newly created user record
            
        Raises:
            Exception: If username already exists or database error occurs
        """
        # VULNERABLE CODE - DO NOT USE IN PRODUCTION
        # Storing password in plain text without hashing
        query = """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """
        return self.db.execute_update(query, (username, password, role))
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password
        
        INTENTIONAL SECURITY VULNERABILITY: Plain text password comparison
        In production, this should compare hashed passwords.
        
        Args:
            username: Username
            password: Password (compared in plain text - INSECURE!)
            
        Returns:
            User dictionary (without password) if authentication successful, None otherwise
        """
        # VULNERABLE CODE - DO NOT USE IN PRODUCTION
        # Comparing plain text passwords
        query = """
            SELECT id, username, role, created_at 
            FROM users 
            WHERE username = ? AND password = ?
        """
        results = self.db.execute_query(query, (username, password))
        return results[0] if results else None
    
    def get_by_username(self, username: str) -> Optional[Dict]:
        """
        Retrieve user by username
        
        Args:
            username: Username to look up
            
        Returns:
            User dictionary (including password - INSECURE!) or None if not found
        """
        query = "SELECT * FROM users WHERE username = ?"
        results = self.db.execute_query(query, (username,))
        return results[0] if results else None
    
    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Retrieve user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User dictionary or None if not found
        """
        query = "SELECT id, username, role, created_at FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def update_password(self, username: str, new_password: str) -> bool:
        """
        Update user password
        
        INTENTIONAL SECURITY VULNERABILITY: Plain text password storage
        
        Args:
            username: Username
            new_password: New password (stored in plain text - INSECURE!)
            
        Returns:
            True if update successful, False otherwise
        """
        # VULNERABLE CODE - DO NOT USE IN PRODUCTION
        query = "UPDATE users SET password = ? WHERE username = ?"
        rows_affected = self.db.execute_update(query, (new_password, username))
        return rows_affected > 0
    
    def delete(self, username: str) -> bool:
        """
        Delete a user account
        
        Args:
            username: Username to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        query = "DELETE FROM users WHERE username = ?"
        rows_affected = self.db.execute_update(query, (username,))
        return rows_affected > 0
    
    def get_all(self) -> list[Dict]:
        """
        Retrieve all users (without passwords)
        
        Returns:
            List of user dictionaries
        """
        query = "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
        return self.db.execute_query(query)
