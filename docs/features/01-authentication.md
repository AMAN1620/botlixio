# Authentication

## Overview

User authentication system supporting email/password registration, JWT-based session management, email verification, password reset, and OAuth login (Google, GitHub). All API access (except public widget and billing plans) requires a valid JWT.

---

## Data Model

See [database-schema.md](../database-schema.md) → `User` model.

Key fields:
- `email`: Unique, used as login identifier
- `password_hash`: bcrypt-hashed, null for OAuth-only users
- `role`: `USER` (default) or `ADMIN`
- `is_verified`: Must be true to create agents
- `auth_provider`: `LOCAL`, `GOOGLE`, `GITHUB`
- `verification_token`, `reset_token`: One-time use tokens with expiry

---

## Pages

### `/login` — Login
- Email + password form
- "Forgot Password?" link
- "Sign up" link
- "Continue with Google" / "Continue with GitHub" buttons
- Error state: "Invalid email or password" (generic, never reveal which is wrong)

### `/register` — Register
- Full name, email, password, confirm password
- Password strength indicator
- "Already have an account? Log in" link
- On submit: POST `/api/v1/auth/register` → redirect to check-email page

### `/verify-email` — Verify Email
- Token in URL query param
- Auto-verifies on page load
- Success: "Email verified! You can now create agents." + redirect to dashboard
- Failure: "Invalid or expired link. Request a new one."

### `/forgot-password` — Forgot Password
- Email input only
- On submit: always shows "If that email exists, you'll receive a reset link" (no email enumeration)

### `/reset-password` — Reset Password
- Token in URL, new password + confirm
- On submit: password updated, redirect to login

---

## Auth Flow — Registration

```
1. User fills form: name, email, password, confirm password
2. Frontend validates (Zod schema: email format, password 8+ chars, passwords match)
3. POST /api/v1/auth/register
4. Backend:
   a. Check email uniqueness → 409 if duplicate
   b. Hash password (bcrypt, cost 12)
   c. Generate verification token (32-byte random hex)
   d. Create User (is_verified=false)
   e. Send verification email via Resend
   f. Return { user: UserResponse }
5. User checks email → clicks link → GET /verify-email?token=xxx
6. POST /api/v1/auth/verify-email { token }
7. Backend validates token, sets is_verified=true
```

---

## Auth Flow — Login

```
1. POST /api/v1/auth/login { email, password }
2. Find user by email → 401 if not found
3. Verify password → 401 if wrong
4. Check is_active → 403 if blocked
5. Create access_token (30 min) + refresh_token (7 days)
6. Update last_login_at
7. Return { access_token, refresh_token, token_type: "bearer" }
```

---

## Auth Flow — Token Refresh

```
1. POST /api/v1/auth/refresh { refresh_token }
2. Decode refresh token → verify not expired
3. Look up user → verify still active
4. Issue new access_token + new refresh_token
5. Invalidate old refresh_token
6. Return { access_token, refresh_token }
```

---

## Auth Flow — Password Reset

```
1. POST /api/v1/auth/forgot-password { email }
2. Find user → if exists, generate reset token (1h expiry)
3. Send reset email (always return 200 regardless)
4. User clicks email link → /reset-password?token=xxx
5. POST /api/v1/auth/reset-password { token, new_password }
6. Validate token not expired → update password_hash → clear token
```

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Duplicate email registration | 409 Conflict with "Email already registered" |
| Login with unverified email | Allow login but restrict agent creation |
| Login with blocked account | 403 Forbidden with "Account blocked" |
| Expired verification token | "Token expired. Request a new one." with resend button |
| Expired reset token | "Reset link has expired. Request a new one." |
| OAuth user tries password login | 400 "Please use {provider} to sign in" |
| Password login user tries OAuth | Link accounts (same email → add oauth_id) |
| Refresh with invalid token | 401 Unauthorized |

---

## Business Rules

1. **Email uniqueness**: One account per email, case-insensitive
2. **Password**: Minimum 8 characters, bcrypt hashed
3. **Verification**: Required to create agents, not required to log in
4. **Token security**: Verification tokens valid 24h, reset tokens valid 1h
5. **No email enumeration**: Forgot-password always returns 200
6. **OAuth linking**: First OAuth login creates account; subsequent logins match by `oauth_id`

---

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login, returns tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/verify-email` | Verify email with token |
| POST | `/api/v1/auth/forgot-password` | Request reset email |
| POST | `/api/v1/auth/reset-password` | Reset password |
| GET | `/api/v1/auth/me` | Get current user |
| GET | `/api/v1/auth/google` | Google OAuth redirect |
| GET | `/api/v1/auth/google/callback` | Google OAuth callback |
