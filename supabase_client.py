"""
Auth client — Postgres + direct Google OAuth.

Previously this module talked to Supabase Auth. Supabase has been removed:
user identity now lives in the `users` table of the app's own PostgreSQL
database (postgres_client.py), and Google sign-in is a standard server-side
OAuth 2.0 authorization-code flow against accounts.google.com.

The public interface (class name, method names, call signatures, and the
shapes returned to app.py) is unchanged, so app.py's auth routes keep
working without modification.
"""

from __future__ import annotations

import os
import json
import base64
import hashlib
import secrets
import urllib.parse
import urllib.request
from contextlib import closing
from datetime import datetime

import psycopg2
import psycopg2.extras
from flask import request, session
from tenant_context import current_tenant_id, normalize_tenant_id, tenant_get, tenant_pop, tenant_set, tenant_key


def _hash_password(password: str, salt: str | None = None) -> str:
    """Hash a password with PBKDF2-SHA256. Returns 'pbkdf2:salt:hash'."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100_000)
    return f"pbkdf2:{salt}:{digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = (stored or '').split(':', 2)
        if scheme != 'pbkdf2':
            return False
    except ValueError:
        return False
    candidate = _hash_password(password, salt)
    return secrets.compare_digest(candidate, stored)


class _AuthUser:
    """Minimal user object matching the attributes app.py reads:
    .id, .email, plus optional profile fields for templates."""

    def __init__(self, id, email, name=None, avatar_url=None):
        self.id = id
        self.email = email
        self.name = name
        self.avatar_url = avatar_url

    def get(self, key, default=None):
        return getattr(self, key, default)


class _AuthResponse:
    """Response shape matching the Supabase SDK results app.py reads:
    res.user / res.session.access_token / res.session.refresh_token"""

    def __init__(self, user=None, session=None):
        self.user = user
        self.session = session


class _AuthSession:
    def __init__(self, access_token, refresh_token=None):
        self.access_token = access_token
        self.refresh_token = refresh_token


class SupabaseAuthStorage:
    # Kept for interface compatibility; no longer used by the auth client.
    def __init__(self):
        pass

    def get_item(self, key: str) -> str | None:
        return tenant_get(key) or tenant_get(f"sb-{key}")

    def set_item(self, key: str, value: str) -> None:
        tenant_set(key, value)

    def remove_item(self, key: str) -> None:
        tenant_pop(key, None)
        tenant_pop(f"sb-{key}", None)


class SupabaseManager:
    """
    Auth manager backed by the app's own PostgreSQL `users` table.

    Sessions are random opaque tokens whose SHA-256 hashes live in the
    `users` table; the browser session only holds the token. Sign-in
    methods return response objects with the same attribute shape the
    Supabase SDK used, so app.py routes are unchanged.
    """

    def __init__(self):
        # Data layer handles its own connection management; we borrow its DSN resolution.
        from postgres_client import _get_database_url
        self._dsn = _get_database_url()

        self._google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self._google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

        # Session token keys in the (tenant-scoped) Flask session.
        self._session_token_key = 'auth_session_token'
        self._refresh_token_key = 'auth_refresh_token'

        self._ensure_users_table()

    def _ensure_users_table(self):
        """Create the users table if it doesn't exist yet (idempotent).
        init_db() in postgres_client.py also creates it; this keeps auth
        self-sufficient even if the data layer hasn't initialized."""
        try:
            with closing(self._conn()) as conn, conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT,
                        google_sub TEXT UNIQUE,
                        name TEXT,
                        avatar_url TEXT,
                        session_token_hash TEXT,
                        refresh_token_hash TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_login_at TIMESTAMP WITH TIME ZONE
                    );
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    CREATE INDEX IF NOT EXISTS idx_users_session_token ON users(session_token_hash);
                """)
                conn.commit()
        except Exception as e:
            print(f"Warning: could not ensure users table: {e}")

    # ── Internal helpers ─────────────────────────────────────────────

    def _conn(self):
        return psycopg2.connect(self._dsn)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _create_session(self, cursor, user_row):
        """Create a session token pair for a user row and persist hashes."""
        token = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        cursor.execute(
            "UPDATE users SET session_token_hash = %s, refresh_token_hash = %s, last_login_at = %s WHERE id = %s",
            (self._hash_token(token),
             self._hash_token(refresh),
             now, user_row['id'])
        )
        return _AuthSession(access_token=token, refresh_token=refresh)

    def _user_by_token(self, token, refresh=False):
        """Look up a user by session (or refresh) token."""
        if not token:
            return None
        column = 'refresh_token_hash' if refresh else 'session_token_hash'
        try:
            with closing(self._conn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"SELECT * FROM users WHERE {column} = %s",
                    (self._hash_token(token),)
                )
                return cur.fetchone()
        except Exception as e:
            print(f"Auth: token lookup error: {e}")
            return None

    def _user_by_email(self, email):
        try:
            with closing(self._conn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", ((email or '').strip().lower(),))
                return cur.fetchone()
        except Exception as e:
            print(f"Auth: email lookup error: {e}")
            return None

    def _get_or_create_google_user(self, google_sub, email, name=None, avatar_url=None):
        email = (email or '').strip().lower()
        try:
            with closing(self._conn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """INSERT INTO users (email, google_sub, name, avatar_url, last_login_at)
                       VALUES (%s, %s, %s, %s, NOW())
                       ON CONFLICT (email) DO UPDATE
                         SET google_sub = COALESCE(EXCLUDED.google_sub, users.google_sub),
                             name = COALESCE(EXCLUDED.name, users.name),
                             avatar_url = COALESCE(EXCLUDED.avatar_url, users.avatar_url),
                             last_login_at = NOW()
                       RETURNING *""",
                    (email, google_sub, name, avatar_url)
                )
                row = cur.fetchone()
                conn.commit()
                return row
        except Exception as e:
            print(f"Auth: google user upsert error: {e}")
            return None

    def _get_or_create_password_user(self, email, password):
        email = (email or '').strip().lower()
        try:
            with closing(self._conn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """INSERT INTO users (email, password_hash, last_login_at)
                       VALUES (%s, %s, NOW())
                       ON CONFLICT (email) DO NOTHING
                       RETURNING *""",
                    (email, _hash_password(password))
                )
                row = cur.fetchone()
                conn.commit()
                return row
        except Exception as e:
            print(f"Auth: password user create error: {e}")
            return None

    def _google_userinfo(self, access_token):
        """Fetch the Google userinfo for an OAuth access token."""
        req = urllib.request.Request(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"Auth: Google userinfo fetch failed: {e}")
            return None

    # ── Auth Methods (same signatures as before) ─────────────────────

    def sign_up(self, email, password, redirect_url=None):
        """Create a local password account. redirect_url is accepted for
        interface compatibility; no verification email is sent."""
        user_row = self._get_or_create_password_user(email, password)
        if not user_row:
            return None
        return _AuthResponse(user=_AuthUser(user_row['id'], user_row['email'], user_row.get('name')))

    def sign_in(self, email, password):
        """Password sign-in. Returns object with .user and .session like the SDK did."""
        user_row = self._user_by_email(email)
        if not user_row or not user_row.get('password_hash') or not _verify_password(password or '', user_row['password_hash']):
            return None
        with closing(self._conn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            auth_session = self._create_session(cur, user_row)
            conn.commit()
        return _AuthResponse(user=_AuthUser(user_row['id'], user_row['email'], user_row.get('name')), session=auth_session)

    def sign_in_with_google(self, redirect_url=None):
        """Return the Google OAuth authorization URL (same .url shape as the SDK result)."""
        if not self._google_client_id or not self._google_client_secret:
            print("Auth: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not configured")
            return None

        # PKCE (S256) for the server-side authorization-code flow
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode('ascii')).digest()
        ).decode('ascii').rstrip('=')

        tenant_set('google_oauth_code_verifier', verifier)

        params = {
            'client_id': self._google_client_id,
            'redirect_uri': redirect_url,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
            'state': secrets.token_urlsafe(16),
        }
        tenant_set('google_oauth_state', params['state'])

        class _OAuthURL:
            pass

        result = _OAuthURL()
        result.url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
        return result

    def exchange_code_for_session(self, code, redirect_to=None, code_verifier=None, **kwargs):
        """Exchange the Google authorization code for a user session.
        Supports the PKCE verifier persisted by sign_in_with_google when
        the caller doesn't pass one explicitly."""
        print(f"Auth: exchanging Google authorization code: {code[:5]}...")

        # CSRF protection: validate the state Google echoed back (when reachable
        # via the request) against the one stored before the redirect.
        stored_state = tenant_get('google_oauth_state')
        if stored_state:
            try:
                returned_state = request.args.get('state')
            except RuntimeError:
                returned_state = None
            if returned_state and returned_state != stored_state:
                print("Auth: OAuth state mismatch — possible CSRF, rejecting")
                raise AuthError("OAuth state mismatch. Please try signing in again.")

        verifier = code_verifier or tenant_get('google_oauth_code_verifier')
        if verifier:
            print(f"Auth: using PKCE code_verifier: {verifier[:5]}...")

        token_endpoint = 'https://oauth2.googleapis.com/token'
        post = urllib.parse.urlencode({
            'code': code,
            'client_id': self._google_client_id,
            'client_secret': self._google_client_secret,
            'redirect_uri': redirect_to,
            'grant_type': 'authorization_code',
            'code_verifier': verifier or '',
        }).encode('utf-8')

        req = urllib.request.Request(token_endpoint, data=post, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                tokens = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'replace')
            print(f"Auth: Google token exchange failed: HTTP {e.code}: {body}")
            raise AuthError(f"Google token exchange failed (HTTP {e.code}). Please try again.") from e

        if tokens.get('error'):
            print(f"Auth: Google token exchange error: {tokens.get('error_description') or tokens.get('error')}")
            raise AuthError(tokens.get('error_description') or tokens.get('error'))

        userinfo = self._google_userinfo(tokens.get('access_token'))
        if not userinfo or not userinfo.get('email'):
            raise AuthError("Could not retrieve Google account email")

        user_row = self._get_or_create_google_user(
            google_sub=userinfo.get('sub'),
            email=userinfo.get('email'),
            name=userinfo.get('name'),
            avatar_url=userinfo.get('picture'),
        )
        if not user_row:
            raise AuthError("Could not create or load user record")

        with closing(self._conn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            auth_session = self._create_session(cur, user_row)
            conn.commit()

        # Clean up the one-time PKCE/state material now that it's consumed
        tenant_pop('google_oauth_code_verifier', None)
        tenant_pop('google_oauth_state', None)

        class _ExchangeResult:
            pass

        result = _ExchangeResult()
        result.session = auth_session
        result.user = _AuthUser(user_row['id'], user_row['email'], user_row.get('name'), user_row.get('avatar_url'))
        print(f"Auth: exchange SUCCESS for {user_row['email']}")
        return result

    def sign_in_with_otp(self, email, redirect_url=None):
        """Magic-link sign-in needs an email provider (Supabase used to be it).
        Returns an error-shaped result; app.py surfaces the message."""

        class _OtpResult:
            pass

        result = _OtpResult()
        result.error = 'magic_link_unavailable'
        result.error_description = (
            "Magic-link sign-in is unavailable because the app no longer uses Supabase. "
            "Please sign in with Google or with your email and password."
        )
        return result

    def sign_out(self):
        """Revoke the current session tokens."""
        token = tenant_get('access_token') or tenant_get(self._session_token_key)
        if not token:
            return None
        try:
            with closing(self._conn()) as conn, conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET session_token_hash = NULL, refresh_token_hash = NULL WHERE session_token_hash = %s",
                    (self._hash_token(token),)
                )
                conn.commit()
        except Exception as e:
            print(f"Auth: sign_out error: {e}")
        finally:
            tenant_pop(self._session_token_key, None)
            tenant_pop(self._refresh_token_key, None)
        return None

    def reset_password(self, email, redirect_url=None):
        """Password reset email needs an email provider (Supabase used to be it).
        Returns an error-shaped result; app.py surfaces the message."""

        class _ResetResult:
            pass

        result = _ResetResult()
        result.error = 'reset_unavailable'
        result.error_description = (
            "Password reset email is unavailable because the app no longer uses Supabase. "
            "Please sign in with Google, or contact support to reset your password."
        )
        return result

    def get_user(self, jwt):
        """Resolve a session token to a user. Same return shape as before:
        object with .user, or None."""
        user_row = self._user_by_token(jwt)
        if not user_row:
            return None
        return _AuthResponse(user=_AuthUser(user_row['id'], user_row['email'], user_row.get('name'), user_row.get('avatar_url')))

    def refresh_session(self, refresh_token):
        """Rotate session tokens given a valid refresh token. Same shape as before."""
        user_row = self._user_by_token(refresh_token, refresh=True)
        if not user_row:
            return None
        with closing(self._conn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            new_session = self._create_session(cur, user_row)
            conn.commit()
        return _AuthResponse(user=_AuthUser(user_row['id'], user_row['email'], user_row.get('name')), session=new_session)

    # ── Data Methods ──────────────────────────────────────────────────
    # Data persistence lives in postgres_client.PostgresManager (get_db_manager).
    # These thin delegates keep any stray call sites working.

    def save_blog_post(self, blog_data, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.save_blog_post(blog_data, user_id=user_id, tenant_id=tenant_id) if db else None

    def get_blog_post_by_id(self, post_id, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.get_blog_post_by_id(post_id, user_id=user_id, tenant_id=tenant_id) if db else None

    def get_recent_posts(self, user_id=None, tenant_id=None, limit=20):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.get_recent_posts(user_id=user_id, tenant_id=tenant_id, limit=limit) if db else []

    def search_posts(self, query_str, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.search_posts(query_str, user_id=user_id, tenant_id=tenant_id) if db else []

    def get_drafts_count(self, user_id, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.get_drafts_count(user_id, tenant_id=tenant_id) if db else 0

    def delete_post(self, post_id, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.delete_post(post_id, user_id=user_id, tenant_id=tenant_id) if db else False

    def get_analytics(self, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.get_analytics(user_id=user_id, tenant_id=tenant_id) if db else None

    def update_post(self, post_id, updates, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.update_post(post_id, updates, user_id=user_id, tenant_id=tenant_id) if db else None

    def save_generation_log(self, log_data, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.save_generation_log(log_data, user_id=user_id, tenant_id=tenant_id) if db else None

    def get_generation_stats(self, user_id=None, tenant_id=None):
        from postgres_client import get_db_manager
        db = get_db_manager()
        return db.get_generation_stats(user_id=user_id, tenant_id=tenant_id) if db else None


class AuthError(Exception):
    """Raised when an OAuth exchange fails; app.py's callback already catches
    generic Exception and renders the message, so no route change is needed."""


def get_supabase_manager():
    try:
        return SupabaseManager()
    except Exception as e:
        print(f"Warning: Auth manager not configured: {e}")
        return None
