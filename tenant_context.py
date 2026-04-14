import json
import os
import re
from flask import has_request_context, request, session, g

DEFAULT_TENANT_ID = re.sub(r'[^a-z0-9._-]+', '-', os.environ.get('DEFAULT_TENANT_ID', 'legacy').strip().lower()) or 'legacy'


def normalize_tenant_id(value):
    if value is None:
        return None
    tenant = str(value).strip().lower()
    if not tenant:
        return None
    tenant = re.sub(r'[^a-z0-9._-]+', '-', tenant)
    tenant = re.sub(r'-{2,}', '-', tenant).strip('._-')
    return tenant or None


def _parse_domain_map():
    raw = os.environ.get('TENANT_DOMAIN_MAP', '').strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {
                str(host).split(':', 1)[0].lower(): normalize_tenant_id(tenant)
                for host, tenant in parsed.items()
                if normalize_tenant_id(tenant)
            }
    except Exception:
        pass
    mapping = {}
    for chunk in raw.split(';'):
        chunk = chunk.strip()
        if not chunk:
            continue
        if '=' in chunk:
            host, tenant = chunk.split('=', 1)
        elif ':' in chunk:
            host, tenant = chunk.split(':', 1)
        else:
            continue
        host = host.strip().lower().split(':', 1)[0]
        tenant = normalize_tenant_id(tenant)
        if host and tenant:
            mapping[host] = tenant
    return mapping


def _request_host():
    if not has_request_context():
        return None
    host = request.headers.get('X-Forwarded-Host') or request.host or request.environ.get('HTTP_HOST') or ''
    return host.split(':', 1)[0].lower().strip()


def _subdomain_tenant(host):
    if not host:
        return None
    if host in {'localhost', '127.0.0.1'}:
        return None
    labels = [label for label in host.split('.') if label]
    if len(labels) < 2:
        return None
    if len(labels) == 2 and labels[-1] != 'localhost':
        return None
    return normalize_tenant_id(labels[0])


def get_session_tenant_id():
    if not has_request_context():
        return None
    return normalize_tenant_id(session.get('active_tenant_id'))


def resolve_tenant_id():
    if not has_request_context():
        return DEFAULT_TENANT_ID

    explicit = request.values.get('tenant_id') or request.values.get('tenant') or request.headers.get('X-Tenant-Id')
    explicit = normalize_tenant_id(explicit)

    host = _request_host()
    domain_map = _parse_domain_map()
    mapped = domain_map.get(host) if host else None
    subdomain = _subdomain_tenant(host)
    request_candidate = explicit or mapped or subdomain

    session_tenant = get_session_tenant_id()
    if session_tenant and request_candidate and session_tenant != request_candidate:
        return None

    return request_candidate or session_tenant or DEFAULT_TENANT_ID


def current_tenant_id():
    if has_request_context():
        tenant_id = normalize_tenant_id(getattr(g, 'tenant_id', None))
        if tenant_id:
            return tenant_id
        tenant_id = get_session_tenant_id()
        if tenant_id:
            return tenant_id
    return DEFAULT_TENANT_ID


def tenant_key(key, tenant_id=None):
    tenant_id = normalize_tenant_id(tenant_id or current_tenant_id()) or DEFAULT_TENANT_ID
    return f'tenant:{tenant_id}:{key}'


def tenant_get(key, default=None, tenant_id=None):
    if not has_request_context():
        return default
    namespaced_key = tenant_key(key, tenant_id)
    if namespaced_key in session:
        return session.get(namespaced_key, default)
    if key in session:
        return session.get(key, default)
    return default


def tenant_set(key, value, tenant_id=None):
    if not has_request_context():
        return
    namespaced_key = tenant_key(key, tenant_id)
    session[namespaced_key] = value
    session.modified = True


def tenant_pop(key, default=None, tenant_id=None):
    if not has_request_context():
        return default
    namespaced_key = tenant_key(key, tenant_id)
    value = session.pop(namespaced_key, default)
    if key in session:
        fallback_value = session.pop(key, default)
        if value is default:
            value = fallback_value
    session.modified = True
    return value


def clear_tenant_session(tenant_id=None):
    if not has_request_context():
        return
    tenant_id = normalize_tenant_id(tenant_id or current_tenant_id()) or DEFAULT_TENANT_ID
    namespaced_prefix = f'tenant:{tenant_id}:'
    legacy_keys = {
        'access_token',
        'refresh_token',
        'user_id',
        'user_email',
        'auth_next_url',
        'current_post_id',
        'generation_params',
        'db_post_id',
        'oauth_state',
        'oauth_nonce',
        'medium_connected',
        'linkedin_connected',
        'sid',
        'supabase.auth.token-code-verifier',
        'sb-supabase.auth.token-code-verifier',
        'supabase.auth.token',
        'sb-supabase.auth.token',
    }
    for key in list(session.keys()):
        if key.startswith(namespaced_prefix) or key in legacy_keys:
            session.pop(key, None)
    if session.get('active_tenant_id') == tenant_id:
        session.pop('active_tenant_id', None)
    session.modified = True


def set_active_tenant_id(tenant_id):
    if not has_request_context():
        return
    tenant_id = normalize_tenant_id(tenant_id) or DEFAULT_TENANT_ID
    session['active_tenant_id'] = tenant_id
    session.modified = True


def tenant_rate_limit_identity(user_id=None):
    if not has_request_context():
        return str(user_id or 'anonymous')
    tenant_id = current_tenant_id()
    actor = str(user_id or request.remote_addr or 'anonymous')
    return f'{tenant_id}:{actor}'
