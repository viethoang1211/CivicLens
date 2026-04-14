"""
Mock VNeID OAuth 2.0 Server for development/demo.

Simulates Vietnam's national digital identity (VNeID) OAuth2 flow:
  1. GET  /authorize       → Login page (shows form to pick a citizen)
  2. POST /authorize       → Validates, redirects with ?code=...
  3. POST /oauth/token      → Exchanges code for access token + user info
  4. GET  /oauth/userinfo   → Returns citizen profile from access token

Citizens are loaded from MOCK_CITIZENS env var (JSON) or defaults to seed data.
"""

import json
import os
import secrets
import time
from urllib.parse import urlencode

from fastapi import FastAPI, Form, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jose import jwt

app = FastAPI(title="Mock VNeID OAuth Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Config ---

JWT_SECRET = os.getenv("VNEID_JWT_SECRET", "mock-vneid-secret-key")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600

# Mock citizen database: list of dicts with id_number, full_name, phone_number
DEFAULT_CITIZENS = [
    {"id_number": "012345678901", "full_name": "Phạm Văn Dũng", "phone_number": "0901234567"},
    {"id_number": "012345678902", "full_name": "Nguyễn Thị Mai", "phone_number": "0912345678"},
    {"id_number": "012345678903", "full_name": "Trần Văn Hùng", "phone_number": "0923456789"},
]

_citizens_json = os.getenv("MOCK_CITIZENS")
CITIZENS: list[dict] = json.loads(_citizens_json) if _citizens_json else DEFAULT_CITIZENS

CITIZENS_BY_ID = {c["id_number"]: c for c in CITIZENS}

# In-memory stores for auth codes and tokens
_auth_codes: dict[str, dict] = {}  # code -> {citizen_id, redirect_uri, expires_at}
_access_tokens: dict[str, dict] = {}  # token -> citizen dict


# --- Authorize endpoint (login page) ---

@app.get("/authorize", response_class=HTMLResponse)
async def authorize_page(
    client_id: str = Query("citizen-app"),
    redirect_uri: str = Query("citizen-app://callback"),
    response_type: str = Query("code"),
    state: str = Query(""),
):
    """Renders a login page where demo user picks a citizen identity."""
    citizen_options = ""
    for c in CITIZENS:
        citizen_options += f'<option value="{c["id_number"]}">{c["full_name"]} — CCCD: {c["id_number"]}</option>\n'

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VNeID - Xác thực danh tính</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%);
                min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .card {{ background: white; border-radius: 16px; padding: 40px; width: 90%; max-width: 420px;
                 box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
        .logo {{ text-align: center; margin-bottom: 24px; }}
        .logo .icon {{ font-size: 48px; }}
        .logo h1 {{ color: #1a237e; font-size: 24px; margin-top: 8px; }}
        .logo p {{ color: #666; font-size: 14px; margin-top: 4px; }}
        .badge {{ display: inline-block; background: #e8f5e9; color: #2e7d32; padding: 4px 12px;
                  border-radius: 12px; font-size: 12px; font-weight: 600; margin-top: 8px; }}
        label {{ display: block; font-weight: 600; color: #333; margin-bottom: 8px; font-size: 14px; }}
        select {{ width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px;
                  font-size: 16px; appearance: auto; background: #fafafa; margin-bottom: 24px; }}
        select:focus {{ border-color: #1a237e; outline: none; }}
        button {{ width: 100%; padding: 14px; background: #1a237e; color: white; border: none;
                  border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;
                  transition: background 0.2s; }}
        button:hover {{ background: #283593; }}
        .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">
            <div class="icon">🛡️</div>
            <h1>VNeID</h1>
            <p>Ứng dụng định danh điện tử quốc gia</p>
            <span class="badge">⚙ MÔI TRƯỜNG DEMO</span>
        </div>
        <form method="POST" action="/authorize">
            <input type="hidden" name="client_id" value="{client_id}">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="hidden" name="response_type" value="{response_type}">
            <input type="hidden" name="state" value="{state}">
            <label for="citizen_id">Chọn tài khoản công dân:</label>
            <select name="citizen_id" id="citizen_id" required>
                <option value="" disabled selected>— Chọn —</option>
                {citizen_options}
            </select>
            <button type="submit">Xác nhận đăng nhập</button>
        </form>
        <div class="footer">Mock VNeID OAuth Server — Chỉ dùng cho demo</div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.post("/authorize")
async def authorize_submit(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form("code"),
    state: str = Form(""),
    citizen_id: str = Form(...),
):
    """Validates citizen selection and redirects with authorization code."""
    if citizen_id not in CITIZENS_BY_ID:
        raise HTTPException(status_code=400, detail="Invalid citizen_id")

    # Generate authorization code
    code = secrets.token_urlsafe(32)
    _auth_codes[code] = {
        "citizen_id": citizen_id,
        "redirect_uri": redirect_uri,
        "expires_at": time.time() + 300,  # 5 min
    }

    # Clean expired codes
    now = time.time()
    expired = [k for k, v in _auth_codes.items() if v["expires_at"] < now]
    for k in expired:
        del _auth_codes[k]

    params = {"code": code}
    if state:
        params["state"] = state
    separator = "&" if "?" in redirect_uri else "?"
    full_redirect = f"{redirect_uri}{separator}{urlencode(params)}"

    # If redirect_uri uses a custom scheme (not http/https), the browser
    # cannot follow it. Show the code on-screen instead so the user can
    # copy-paste it into the app (common for web/emulator demo).
    if not redirect_uri.startswith(("http://", "https://")):
        citizen = CITIZENS_BY_ID[citizen_id]
        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VNeID - Đăng nhập thành công</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #43a047 100%);
                min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .card {{ background: white; border-radius: 16px; padding: 40px; width: 90%; max-width: 480px;
                 box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; }}
        .icon {{ font-size: 48px; margin-bottom: 16px; }}
        h1 {{ color: #1b5e20; font-size: 22px; margin-bottom: 8px; }}
        .citizen {{ color: #666; font-size: 16px; margin-bottom: 24px; }}
        .code-box {{ background: #f5f5f5; border: 2px dashed #43a047; border-radius: 12px;
                     padding: 20px; margin-bottom: 16px; }}
        .code-label {{ font-size: 13px; color: #888; margin-bottom: 8px; }}
        .code {{ font-family: 'Courier New', monospace; font-size: 14px; word-break: break-all;
                 color: #1b5e20; font-weight: 700; user-select: all; }}
        button {{ padding: 12px 32px; background: #1b5e20; color: white; border: none;
                  border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer;
                  transition: background 0.2s; }}
        button:hover {{ background: #2e7d32; }}
        .hint {{ color: #999; font-size: 12px; margin-top: 16px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">✅</div>
        <h1>Xác thực thành công!</h1>
        <div class="citizen">{citizen["full_name"]} — CCCD: {citizen["id_number"]}</div>
        <div class="code-box">
            <div class="code-label">Mã xác thực (copy và dán vào app):</div>
            <div class="code" id="authCode">{code}</div>
        </div>
        <button onclick="navigator.clipboard.writeText(document.getElementById('authCode').textContent).then(()=>this.textContent='Đã copy ✓')">
            📋 Copy mã
        </button>
        <div class="hint">Quay lại ứng dụng và dán mã này để hoàn tất đăng nhập</div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html)

    return RedirectResponse(
        url=full_redirect,
        status_code=302,
    )


# --- Token endpoint ---

@app.post("/oauth/token")
async def token_exchange(request: Request):
    """Exchange authorization code for access token."""
    # Accept both form and JSON
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        body = await request.json()
    else:
        form = await request.form()
        body = dict(form)

    code = body.get("code", "")
    grant_type = body.get("grant_type", "authorization_code")

    if grant_type != "authorization_code":
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)

    auth_entry = _auth_codes.pop(code, None)
    if auth_entry is None or auth_entry["expires_at"] < time.time():
        return JSONResponse({"error": "invalid_grant", "error_description": "Invalid or expired authorization code"}, status_code=400)

    citizen = CITIZENS_BY_ID[auth_entry["citizen_id"]]

    # Issue JWT access token with citizen info
    payload = {
        "sub": citizen["id_number"],
        "full_name": citizen["full_name"],
        "phone_number": citizen.get("phone_number", ""),
        "iss": "mock-vneid",
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }
    access_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Store for userinfo endpoint
    _access_tokens[access_token] = citizen

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": TOKEN_EXPIRE_SECONDS,
        "scope": "openid profile",
        "id_token": access_token,
    }


# --- UserInfo endpoint ---

@app.get("/oauth/userinfo")
async def userinfo(request: Request):
    """Returns citizen profile from Bearer token."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "sub": payload["sub"],
        "full_name": payload["full_name"],
        "phone_number": payload.get("phone_number", ""),
        "id_number": payload["sub"],
    }


# --- Health check ---

@app.get("/health")
async def health():
    return {"status": "ok", "service": "mock-vneid"}


# --- Well-known OpenID config ---

@app.get("/.well-known/openid-configuration")
async def openid_config(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "userinfo_endpoint": f"{base}/oauth/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
    }
