# Authentication and Security

> **What is this?** This covers the core principles of protecting users in a web application: securely hashing passwords, issuing JSON Web Tokens (JWT) for stateless sessions, and implementing stateful token rotation to block reuse.

---

## Key Concepts

### Hashing Passwords with bcrypt
Never store passwords in plaintext! We use `passlib` configured with the `bcrypt` algorithm. Hashing transforms a password into an irreversible random-looking string. When a user logs in, we hash their input password and compare it to the stored hash. We add a unique "salt" string so even identical passwords have different hashes.

### JSON Web Tokens (JWT)
We use `python-jose` to create JWTs. A JWT is a three-part Base64 string (Header.Payload.Signature). 
It contains claims (data like a user ID or expiration time) that are digitally signed. The signature ensures the client cannot tamper with the data without invalidating the token.

### Stateful Token Revocation (Refresh Token Rotation)
Access tokens have short lifespans (e.g. 15 minutes), and Refresh tokens have long lifespans (e.g. 7 days). To prevent stolen refresh tokens from being reused indefinitely, we use **rotation**.
When a user trades their refresh token for a new set of tokens, we issue a new refresh token and invalidate the old one. We persist the SHA-256 hash of the currently active request token onto the user's database row.

---

## Code Examples

### JWT Creation (`backend/app/core/security.py`)

```python
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from jose import jwt

def create_refresh_token(user_id: str) -> str:
    """Creates a JWT designed for token rotation with a unique tracking ID."""
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()), # JWT ID to prevent collision
        "exp": expire,
    }
    return jwt.encode(payload, "secret-key", algorithm="HS256")
```

**What this does:**
We generate a dictionary (payload) with the user ID (`sub`). The token has a specific `type` to ensure access tokens and refresh tokens can't be swapped. The `jti` is a guaranteed-unique UUID per token. Ultimately, `jwt.encode` turns this block into a verifiable string signed with the application's secret key.

### Hashing the Refresh Token for the Database

```python
def hash_refresh_token(token: str) -> str:
    """Transforms the JWT string into a persistent hash to store in the DB."""
    return hashlib.sha256(token.encode()).hexdigest()
```

**What this does:**
Instead of storing the literal refresh token string in the DB (which would be a security risk if the database leaks), we store a fast SHA-256 hex digest. When a client tries to `/refresh`, they provide the raw token; we compute its hash and compare it to the `refresh_token_hash` securely persisted in the database.

---

## Gotchas & Tips

- **JWT Collision during sub-second execution**: JWT standard expiration limits (`exp`) only resolve down to the *second*. If a user requests a new token rapidly (or your test invokes rotations extremely quickly), the new JWT might be byte-for-byte identical to the old one. To fix this, always inject a UUID into the `jti` (JWT ID) claim so that every generated token has a guaranteed unique signature, forcing different hashes.
- **Passlib limitations in Python 3.13+**: The library default for `passlib` uses python's deprecated auto-detection paths. Avoid auto-deprecated settings by pinning specific algorithm configurations via `CryptContext(schemes=["bcrypt"], deprecated="auto")`.
- **Stateless vs Stateful**: JWT is natively *stateless*. But for deep security (like enforcing revocation or immediate banning), augmenting JWT with a *stateful* mechanism (like validating hashes over the database) yields the best trade-off of speed and security.

---

## See Also
- [sqlalchemy-async.md](sqlalchemy-async.md) — How the repository layer stores our generated token hashes.
- `docs/database-schema.md` — Explains the structure storing `password_hash` and `refresh_token_hash`.
