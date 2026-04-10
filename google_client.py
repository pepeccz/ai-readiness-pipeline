"""
Google API client using Service Account authentication.
Replaces all gog CLI calls with direct API access.
Provides: Sheets read/write, Drive upload, Gmail send (with Resend fallback).
"""

import json
import os
import requests as http_requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

from config import settings

# --- Scopes ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]

# --- Credential singleton ---
_credentials: service_account.Credentials | None = None


def get_credentials() -> service_account.Credentials:
    """Return cached service account credentials, refreshing if needed."""
    global _credentials
    if _credentials is None:
        sa_info = settings.get_sa_info()
        _credentials = service_account.Credentials.from_service_account_info(
            sa_info, scopes=SCOPES
        )
    if _credentials.expired or not _credentials.token:
        _credentials.refresh(Request())
    return _credentials


def get_access_token() -> str:
    """Return a valid access token string."""
    creds = get_credentials()
    if not creds.token:
        creds.refresh(Request())
    return creds.token


def get_delegated_credentials(user_email: str = None) -> service_account.Credentials:
    """Return credentials delegated to a specific user (for Gmail impersonation)."""
    email = user_email or settings.google_delegated_user
    sa_info = settings.get_sa_info()
    creds = service_account.Credentials.from_service_account_info(
        sa_info, scopes=SCOPES, subject=email
    )
    creds.refresh(Request())
    return creds


# --- Sheets API ---


def sheets_read(sheet_id: str, range_str: str) -> list:
    """
    Read values from a Google Sheet range.
    Returns list of rows (each row is a list of cell values).
    """
    token = get_access_token()
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        f"/values/{range_str}"
    )
    r = http_requests.get(
        url, headers={"Authorization": f"Bearer {token}"}, timeout=30
    )
    r.raise_for_status()
    return r.json().get("values", [])


def sheets_batch_update(sheet_id: str, data: list[dict], token: str = None) -> dict:
    """
    Write multiple ranges to a Google Sheet.
    data: list of {"range": "Sheet!A1", "values": [[...]]}
    """
    if token is None:
        token = get_access_token()
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        f"/values:batchUpdate"
    )
    body = {
        "valueInputOption": "RAW",
        "data": data,
    }
    r = http_requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


# --- Drive API ---


def drive_upload(
    file_path: str,
    folder_id: str,
    company_name: str = "",
    mime: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
) -> dict:
    """Upload a file to Google Drive. Returns {id, webViewLink}."""
    token = get_access_token()
    fname = os.path.basename(file_path)
    meta = {"name": fname, "parents": [folder_id]}
    boundary = "----MultipartBoundary"

    with open(file_path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Type: application/json; charset=UTF-8\r\n\r\n'
        f"{json.dumps(meta)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime}\r\n"
        f"Content-Transfer-Encoding: binary\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--".encode("utf-8")

    r = http_requests.post(
        "https://www.googleapis.com/upload/drive/v3/files"
        "?uploadType=multipart&fields=id,webViewLink",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        data=body,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


# --- Gmail API ---


def gmail_send(to: str, subject: str, body_text: str) -> bool:
    """
    Send an email via Gmail API (using delegated SA credentials).
    Falls back to Resend API if Gmail delegation fails.
    Returns True on success.
    """
    # Try Gmail API first
    try:
        return _gmail_send_api(to, subject, body_text)
    except Exception as e:
        print(f"   [google_client] Gmail API falló: {e}")

    # Fallback: Resend
    resend_key = settings.resend_api_key.get_secret_value()
    if resend_key:
        try:
            return _resend_send(to, subject, body_text, resend_key)
        except Exception as e:
            print(f"   [google_client] Resend falló: {e}")

    print("   [google_client] ⚠ No se pudo enviar email por ningún método")
    return False


def _gmail_send_api(to: str, subject: str, body_text: str) -> bool:
    """Send email via Gmail API with domain-wide delegation."""
    import base64
    from email.mime.text import MIMEText

    creds = get_delegated_credentials()

    message = MIMEText(body_text, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject
    message["from"] = settings.google_delegated_user

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    r = http_requests.post(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        },
        json={"raw": raw},
        timeout=30,
    )
    r.raise_for_status()
    print(f"   [google_client] Email enviado via Gmail API a {to}")
    return True


def _resend_send(to: str, subject: str, body_text: str, api_key: str) -> bool:
    """Send email via Resend API (fallback)."""
    r = http_requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": f"Natalia <natalia@zanovix.com>",
            "to": [to],
            "subject": subject,
            "text": body_text,
        },
        timeout=30,
    )
    r.raise_for_status()
    print(f"   [google_client] Email enviado via Resend a {to}")
    return True
