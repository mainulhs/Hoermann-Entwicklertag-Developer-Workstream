# Security Issues Guide

This document describes the intentional security vulnerabilities included in the Industrial Monitoring System for educational purposes. Each vulnerability includes hints for discovery and guidance for remediation using AI-assisted development tools.

⚠️ **WARNING**: This application contains intentional security flaws and should NEVER be deployed to production environments.

## Overview

The application contains five major categories of security vulnerabilities:

1. SQL Injection
2. Hardcoded Secrets
3. Insecure Password Storage
4. Missing Authentication
5. Weak Token Generation

## Vulnerability 1: SQL Injection

### Description

The equipment search functionality is vulnerable to SQL injection attacks, allowing attackers to execute arbitrary SQL commands.

### Location

**File**: `repositories/equipment.py`  
**Method**: `EquipmentRepository.search()`

### Hints for Discovery

1. Look for string concatenation or f-strings used to build SQL queries
2. Search for queries that include user input without parameterization
3. Try searching for equipment with input like: `' OR '1'='1`
4. Use AI tools to scan for SQL injection patterns:
   - "Find SQL injection vulnerabilities in this codebase"
   - "Analyze database query construction for security issues"

### Vulnerable Code Pattern

```python
def search(self, query: str) -> List[Dict]:
    # VULNERABLE: User input directly concatenated into SQL
    sql = f"SELECT * FROM equipment WHERE name LIKE '%{query}%'"
    return self.db.execute_query(sql, ())
```

### Attack Example

```bash
# Malicious input that returns all equipment
curl -X GET "http://localhost:5000/api/equipment?search=' OR '1'='1"

# Malicious input that could drop tables
curl -X GET "http://localhost:5000/api/equipment?search='; DROP TABLE equipment; --"
```

### Remediation Guidance

**AI Prompts to Use:**
- "Fix the SQL injection vulnerability in the search method"
- "Rewrite this query using parameterized statements"
- "Show me how to safely handle user input in SQL queries"

**Secure Implementation:**

```python
def search(self, query: str) -> List[Dict]:
    # SECURE: Use parameterized query
    sql = "SELECT * FROM equipment WHERE name LIKE ?"
    return self.db.execute_query(sql, (f'%{query}%',))
```

**Key Principles:**
- Always use parameterized queries (prepared statements)
- Never concatenate user input into SQL strings
- Use the database driver's parameter substitution (? or %s placeholders)
- Validate and sanitize input as an additional layer of defense

### Validation

After fixing, verify the vulnerability is resolved:

```bash
# This should return only matching equipment, not all records
curl -X GET "http://localhost:5000/api/equipment?search=' OR '1'='1"
```

Run property-based tests to ensure correctness:

```bash
pytest test_equipment_properties.py -v
```

---

## Vulnerability 2: Hardcoded Secrets

### Description

Sensitive credentials and API keys are hardcoded directly in the source code, making them visible to anyone with access to the repository.

### Location

**File**: `config.py`  
**Class**: `Config`

### Hints for Discovery

1. Search for strings like "SECRET_KEY", "API_KEY", "password", "token"
2. Look for hardcoded values in configuration classes
3. Use AI tools to scan for secrets:
   - "Find hardcoded secrets and credentials in this code"
   - "Scan for security keys that should be in environment variables"
4. Use tools like `git-secrets` or `truffleHog` to detect secrets

### Vulnerable Code Pattern

```python
class Config:
    # VULNERABLE: Hardcoded secrets
    SECRET_KEY = "hardcoded-secret-key-12345"
    API_KEY = "sk_live_abc123xyz789"
    DATABASE_PASSWORD = "admin123"
```

### Security Impact

- Secrets are visible in version control history
- Anyone with repository access can extract credentials
- Secrets cannot be rotated without code changes
- Different environments (dev/staging/prod) share the same secrets

### Remediation Guidance

**AI Prompts to Use:**
- "Move hardcoded secrets to environment variables"
- "Show me how to use python-dotenv for configuration"
- "Implement secure configuration management for Flask"

**Secure Implementation:**

```python
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()  # Load from .env file
        
        # SECURE: Read from environment variables
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        self.API_KEY = os.environ.get('API_KEY')
        self.DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
        
        # Validate required secrets are present
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required")
```

**Environment File (.env):**

```bash
# .env file (add to .gitignore!)
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
DATABASE_PASSWORD=your-db-password-here
```

**Key Principles:**
- Store secrets in environment variables or secure vaults
- Never commit secrets to version control
- Add `.env` files to `.gitignore`
- Use different secrets for different environments
- Rotate secrets regularly
- Use secret management services (AWS Secrets Manager, HashiCorp Vault) in production

### Validation

After fixing:

1. Verify secrets are not in source code:
   ```bash
   grep -r "hardcoded-secret" .
   ```

2. Ensure application reads from environment:
   ```bash
   export SECRET_KEY="test-key"
   python app.py
   ```

---

## Vulnerability 3: Insecure Password Storage

### Description

User passwords are stored in plain text in the database, allowing anyone with database access to read all user credentials.

### Location

**File**: `repositories/users.py`  
**Methods**: `UserRepository.create()` and `UserRepository.authenticate()`

### Hints for Discovery

1. Examine how passwords are stored in the database
2. Look at the users table schema - is there any hashing?
3. Check if passwords are compared directly as strings
4. Use AI tools:
   - "Analyze password storage security in this authentication code"
   - "Find insecure password handling"

### Vulnerable Code Pattern

```python
class UserRepository:
    def create(self, username: str, password: str) -> int:
        # VULNERABLE: Plain text password storage
        sql = "INSERT INTO users (username, password) VALUES (?, ?)"
        return self.db.execute_update(sql, (username, password))
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        # VULNERABLE: Direct string comparison
        sql = "SELECT * FROM users WHERE username = ? AND password = ?"
        results = self.db.execute_query(sql, (username, password))
        return results[0] if results else None
```

### Security Impact

- Database breach exposes all user passwords
- Administrators can see user passwords
- Passwords visible in database backups
- Compliance violations (GDPR, PCI-DSS, etc.)

### Remediation Guidance

**AI Prompts to Use:**
- "Implement secure password hashing using bcrypt"
- "Fix insecure password storage in this authentication code"
- "Show me how to use werkzeug.security for password hashing"

**Secure Implementation:**

```python
from werkzeug.security import generate_password_hash, check_password_hash

class UserRepository:
    def create(self, username: str, password: str) -> int:
        # SECURE: Hash password before storage
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        sql = "INSERT INTO users (username, password) VALUES (?, ?)"
        return self.db.execute_update(sql, (username, password_hash))
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        # SECURE: Retrieve hash and verify
        sql = "SELECT * FROM users WHERE username = ?"
        results = self.db.execute_query(sql, (username,))
        
        if not results:
            return None
        
        user = results[0]
        if check_password_hash(user['password'], password):
            return user
        return None
```

**Key Principles:**
- Always hash passwords before storage
- Use strong hashing algorithms (bcrypt, Argon2, PBKDF2)
- Add salt to prevent rainbow table attacks (automatic with modern libraries)
- Never log or display passwords
- Use constant-time comparison to prevent timing attacks

### Validation

After fixing:

1. Create a test user and verify password is hashed:
   ```bash
   sqlite3 industrial_monitoring.db "SELECT password FROM users WHERE username='testuser'"
   # Should see a hash like: pbkdf2:sha256:...
   ```

2. Verify authentication still works:
   ```bash
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass"}'
   ```

Run authentication property tests:

```bash
pytest test_auth_properties.py -v
```

---

## Vulnerability 4: Missing Authentication

### Description

Sensitive API endpoints lack authentication checks, allowing unauthorized users to perform privileged operations.

### Location

**File**: `routes/api.py`  
**Endpoint**: `DELETE /api/equipment/<id>`

### Hints for Discovery

1. Test API endpoints without authentication tokens
2. Look for endpoints missing `@require_auth` decorators
3. Check if DELETE operations require authorization
4. Use AI tools:
   - "Find API endpoints missing authentication"
   - "Analyze authorization checks in API routes"

### Vulnerable Code Pattern

```python
# VULNERABLE: No authentication required
@app.route('/api/equipment/<equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id):
    # Anyone can delete equipment!
    result = equipment_manager.delete_equipment(equipment_id)
    return jsonify(result)
```

### Attack Example

```bash
# Unauthorized deletion - should fail but doesn't!
curl -X DELETE http://localhost:5000/api/equipment/PUMP-001
```

### Security Impact

- Unauthorized data deletion
- Data integrity violations
- Potential for sabotage or vandalism
- Compliance violations

### Remediation Guidance

**AI Prompts to Use:**
- "Add authentication to this API endpoint"
- "Implement a require_auth decorator for Flask"
- "Show me how to protect sensitive endpoints"

**Secure Implementation:**

```python
from functools import wraps
from flask import request, jsonify

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        user = auth_service.validate_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

# SECURE: Authentication required
@app.route('/api/equipment/<equipment_id>', methods=['DELETE'])
@require_auth
def delete_equipment(equipment_id):
    result = equipment_manager.delete_equipment(equipment_id)
    return jsonify(result)
```

**Key Principles:**
- Require authentication for all sensitive operations
- Use decorators for consistent authentication enforcement
- Validate tokens on every request
- Implement role-based access control (RBAC) for fine-grained permissions
- Return appropriate HTTP status codes (401 for authentication, 403 for authorization)

### Validation

After fixing:

1. Test without authentication (should fail):
   ```bash
   curl -X DELETE http://localhost:5000/api/equipment/PUMP-001
   # Should return 401 Unauthorized
   ```

2. Test with valid token (should succeed):
   ```bash
   TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}' | jq -r '.token')
   
   curl -X DELETE http://localhost:5000/api/equipment/PUMP-001 \
     -H "Authorization: Bearer $TOKEN"
   # Should return 200 OK
   ```

---

## Vulnerability 5: Weak Token Generation

### Description

Authentication tokens are generated using weak randomness and lack expiration, making them predictable and allowing indefinite access.

### Location

**File**: `services/auth_service.py`  
**Method**: `AuthService.generate_token()`

### Hints for Discovery

1. Examine token generation logic
2. Check if tokens have expiration times
3. Look for use of `random` instead of `secrets` module
4. Use AI tools:
   - "Analyze token generation security"
   - "Find weak random number generation"

### Vulnerable Code Pattern

```python
import random

class AuthService:
    def generate_token(self, username: str) -> str:
        # VULNERABLE: Predictable token generation
        return f"{username}_{random.randint(1000, 9999)}"
    
    def validate_token(self, token: str) -> Optional[Dict]:
        # VULNERABLE: No expiration check
        return self.token_store.get(token)
```

### Security Impact

- Tokens can be guessed or brute-forced
- Stolen tokens work indefinitely
- No way to force re-authentication
- Session hijacking risks

### Remediation Guidance

**AI Prompts to Use:**
- "Implement secure token generation with expiration"
- "Use JWT tokens for authentication"
- "Fix weak random token generation"

**Secure Implementation:**

```python
import secrets
import jwt
from datetime import datetime, timedelta

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, username: str) -> str:
        # SECURE: Cryptographically secure token with expiration
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_token(self, token: str) -> Optional[Dict]:
        # SECURE: Verify signature and expiration
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {'username': payload['username']}
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Invalid token
```

**Alternative (Simple Token):**

```python
import secrets
from datetime import datetime, timedelta

class AuthService:
    def generate_token(self, username: str) -> str:
        # SECURE: Cryptographically secure random token
        token = secrets.token_urlsafe(32)
        expiration = datetime.utcnow() + timedelta(hours=24)
        
        # Store token with expiration
        self.token_store[token] = {
            'username': username,
            'expires_at': expiration
        }
        return token
    
    def validate_token(self, token: str) -> Optional[Dict]:
        # SECURE: Check existence and expiration
        token_data = self.token_store.get(token)
        
        if not token_data:
            return None
        
        if datetime.utcnow() > token_data['expires_at']:
            # Token expired, remove it
            del self.token_store[token]
            return None
        
        return {'username': token_data['username']}
```

**Key Principles:**
- Use cryptographically secure random generation (`secrets` module)
- Implement token expiration
- Use standard formats like JWT when appropriate
- Store minimal data in tokens
- Implement token refresh mechanisms
- Allow token revocation

### Validation

After fixing:

1. Verify tokens are unpredictable:
   ```bash
   # Generate multiple tokens - should be completely different
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"user1","password":"pass1"}'
   ```

2. Test token expiration (if using short expiration for testing):
   ```bash
   # Wait for expiration period, then try to use token
   curl -X GET http://localhost:5000/api/equipment \
     -H "Authorization: Bearer $EXPIRED_TOKEN"
   # Should return 401 Unauthorized
   ```

Run authentication property tests:

```bash
pytest test_auth_properties.py::test_expired_token_rejection -v
```

---

## General Security Best Practices

After remediating the specific vulnerabilities, consider these additional security improvements:

### Input Validation

- Validate all user input on the server side
- Use allowlists rather than denylists
- Sanitize input before processing
- Implement rate limiting to prevent abuse

### HTTPS/TLS

- Use HTTPS in production (not applicable for local workshop)
- Enforce secure cookie flags (Secure, HttpOnly, SameSite)
- Implement HSTS headers

### Error Handling

- Don't expose sensitive information in error messages
- Log security events for monitoring
- Implement proper exception handling

### Dependencies

- Keep dependencies up to date
- Use `pip-audit` to scan for known vulnerabilities
- Pin dependency versions in requirements.txt

### Code Review

- Use AI tools for security scanning
- Implement peer review processes
- Run automated security tests in CI/CD

## Workshop Exercise Checklist

Use this checklist to track your progress:

- [ ] Discovered SQL injection vulnerability
- [ ] Fixed SQL injection using parameterized queries
- [ ] Discovered hardcoded secrets
- [ ] Moved secrets to environment variables
- [ ] Discovered plain text password storage
- [ ] Implemented password hashing
- [ ] Discovered missing authentication
- [ ] Added authentication to sensitive endpoints
- [ ] Discovered weak token generation
- [ ] Implemented secure token generation with expiration
- [ ] Verified all fixes with property-based tests
- [ ] Documented lessons learned

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Flask Security Considerations](https://flask.palletsprojects.com/en/3.0.x/security/)
- [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

---

**Remember**: These vulnerabilities are intentional for educational purposes. Always follow security best practices in real applications!
