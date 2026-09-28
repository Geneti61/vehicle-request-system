
# ============================================================
# EPSS Vehicle System - Persistence Layer
# Reads/writes data to Google Sheets so it survives restarts
# ============================================================

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def get_client():
    """Create the gspread client from Streamlit Secrets."""
    try:
        creds_dict = dict(st.secrets["google"]["service_account"])
        # Fix the private key newlines if they came through with literal \n
        if "\\n" in creds_dict["private_key"]:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Could not connect to Google Sheets: {e}")
        return None


def get_sheet():
    """Return the storage spreadsheet object."""
    client = get_client()
    if client is None:
        return None
    try:
        sheet_id = st.secrets["google"]["sheet_id"]
        return client.open_by_key(sheet_id)
    except Exception as e:
        st.error(f"Could not open the sheet: {e}")
        return None


def load_requests():
    """Load all requests from the 'Requests' tab."""
    sheet = get_sheet()
    if sheet is None:
        return []
    try:
        worksheet = sheet.worksheet("Requests")
        records = worksheet.get_all_values()
        requests = []
        for row in records[1:]:  # skip header
            if row and row[0]:
                try:
                    requests.append(json.loads(row[0]))
                except Exception:
                    pass
        return requests
    except Exception as e:
        st.warning(f"Could not load requests: {e}")
        return []


def save_requests(requests_list):
    """Save all requests to the 'Requests' tab (overwrites)."""
    sheet = get_sheet()
    if sheet is None:
        return False
    try:
        worksheet = sheet.worksheet("Requests")
        worksheet.clear()
        data = [["data"]]
        for r in requests_list:
            data.append([json.dumps(r, default=str)])
        worksheet.update(values=data, range_name="A1")
        return True
    except Exception as e:
        st.warning(f"Could not save requests: {e}")
        return False


def append_audit(action, user_email, request_id):
    """Append one line to AuditLog."""
    sheet = get_sheet()
    if sheet is None:
        return False
    try:
        worksheet = sheet.worksheet("AuditLog")
        from datetime import datetime
        line = json.dumps({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_email,
            "action": action,
            "request_id": request_id,
        })
        worksheet.append_row([line])
        return True
    except Exception as e:
        return False
