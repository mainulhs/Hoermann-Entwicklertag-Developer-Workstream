"""
Property-Based Tests for Authentication
Tests authentication and authorization properties

Properties tested:
- Property 25: Valid credential authentication
- Property 26: Token generation on success
- Property 27: Invalid credential rejection
- Property 28: Protected endpoint authorization
- Property 29: Expired token rejection
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from database import DatabaseManager
from repositories.users import UserRepository
from services.auth_service import AuthService
import os
import tempfile


def create_auth_service():
    """Create a fresh AuthService instance with temporary database"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = DatabaseManager(db_path)
    
    # Initialize schema
    schema_sql = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'operator',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    cursor.close()
    
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    
    return auth_service, db, db_path


# Hypothesis strategies
username_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'),
    min_size=3,
    max_size=20
)

password_strategy = st.text(min_size=6, max_size=50)

role_strategy = st.sampled_from(['operator', 'technician', 'manager', 'admin'])


# Feature: industrial-monitoring-system, Property 25: Valid credential authentication
@given(
    username=username_strategy,
    password=password_strategy,
    role=role_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_valid_credential_authentication(username, password, role):
    """
    Property 25: Valid credential authentication
    For any user with stored credentials, providing the correct username and password
    should result in successful authentication
    
    **Validates: Requirements 7.1**
    """
    auth_service, db, db_path = create_auth_service()
    
    try:
        # Create user
        result = auth_service.create_user(username, password, role)
        
        # Skip if username already exists (from previous test iteration)
        if not result.success:
            return
        
        # Attempt login with correct credentials
        token = auth_service.login(username, password)
        
        # Should successfully authenticate
        assert token is not None, "Login with valid credentials should return a token"
        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"
    finally:
        db.close()
        os.unlink(db_path)


# Feature: industrial-monitoring-system, Property 26: Token generation on success
@given(
    username=username_strategy,
    password=password_strategy,
    role=role_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_token_generation_on_success(username, password, role):
    """
    Property 26: Token generation on success
    For any successful authentication, the system should return an authentication token
    
    **Validates: Requirements 7.2**
    """
    auth_service, db, db_path = create_auth_service()
    
    try:
        # Create user
        result = auth_service.create_user(username, password, role)
        
        # Skip if username already exists
        if not result.success:
            return
        
        # Login
        token = auth_service.login(username, password)
        
        # Should return a token
        assert token is not None, "Successful login should return a token"
        
        # Token should be valid
        user_info = auth_service.validate_token(token)
        assert user_info is not None, "Generated token should be valid"
        assert user_info['username'] == username, "Token should contain correct username"
        assert user_info['role'] == role, "Token should contain correct role"
    finally:
        db.close()
        os.unlink(db_path)


# Feature: industrial-monitoring-system, Property 27: Invalid credential rejection
@given(
    username=username_strategy,
    correct_password=password_strategy,
    wrong_password=password_strategy,
    role=role_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_invalid_credential_rejection(username, correct_password, wrong_password, role):
    """
    Property 27: Invalid credential rejection
    For any authentication attempt with incorrect username or password,
    the system should reject the request with an error message
    
    **Validates: Requirements 7.3**
    """
    # Ensure passwords are different
    if correct_password == wrong_password:
        return
    
    auth_service, db, db_path = create_auth_service()
    
    try:
        # Create user with correct password
        result = auth_service.create_user(username, correct_password, role)
        
        # Skip if username already exists
        if not result.success:
            return
        
        # Attempt login with wrong password
        token = auth_service.login(username, wrong_password)
        
        # Should fail to authenticate
        assert token is None, "Login with incorrect password should return None"
        
        # Also test with non-existent username
        fake_username = username + "_fake_suffix_xyz"
        token2 = auth_service.login(fake_username, correct_password)
        
        assert token2 is None, "Login with non-existent username should return None"
    finally:
        db.close()
        os.unlink(db_path)


# Feature: industrial-monitoring-system, Property 28: Protected endpoint authorization
@given(
    username=username_strategy,
    password=password_strategy,
    role=role_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_protected_endpoint_authorization(username, password, role):
    """
    Property 28: Protected endpoint authorization
    For any protected API endpoint, requests without a valid authentication token
    should be rejected
    
    **Validates: Requirements 7.4**
    """
    auth_service, db, db_path = create_auth_service()
    
    try:
        # Create user
        result = auth_service.create_user(username, password, role)
        
        # Skip if username already exists
        if not result.success:
            return
        
        # Test with no token
        try:
            auth_service.require_auth(None)
            assert False, "require_auth with no token should raise AuthenticationError"
        except Exception as e:
            assert "Authentication token required" in str(e)
        
        # Test with invalid token
        try:
            auth_service.require_auth("invalid_token_xyz")
            assert False, "require_auth with invalid token should raise AuthenticationError"
        except Exception as e:
            assert "Invalid or expired" in str(e)
        
        # Test with valid token (should succeed)
        token = auth_service.login(username, password)
        user_info = auth_service.require_auth(token)
        
        assert user_info is not None, "require_auth with valid token should return user info"
        assert user_info['username'] == username
    finally:
        db.close()
        os.unlink(db_path)


# Feature: industrial-monitoring-system, Property 29: Expired token rejection
@given(
    username=username_strategy,
    password=password_strategy,
    role=role_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_expired_token_rejection(username, password, role):
    """
    Property 29: Expired token rejection
    For any expired authentication token, requests using that token should be rejected
    and require re-authentication
    
    NOTE: Current implementation has INTENTIONAL FLAW - tokens never expire!
    This test documents the expected behavior, but will pass with the flawed implementation
    because we can't actually test expiration without a working expiration mechanism.
    
    **Validates: Requirements 7.5**
    """
    auth_service, db, db_path = create_auth_service()
    
    try:
        # Create user
        result = auth_service.create_user(username, password, role)
        
        # Skip if username already exists
        if not result.success:
            return
        
        # Login to get token
        token = auth_service.login(username, password)
        assert token is not None
        
        # Logout (invalidate token)
        success = auth_service.logout(token)
        assert success, "Logout should succeed"
        
        # Token should now be invalid
        user_info = auth_service.validate_token(token)
        assert user_info is None, "Token should be invalid after logout"
        
        # Attempting to use invalidated token should fail
        try:
            auth_service.require_auth(token)
            assert False, "require_auth with logged out token should raise AuthenticationError"
        except Exception as e:
            assert "Invalid or expired" in str(e)
        
        # NOTE: We cannot test actual time-based expiration because the current
        # implementation doesn't implement it (INTENTIONAL FLAW for workshop)
    finally:
        db.close()
        os.unlink(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
