import requests
import json
import os
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

WORKERS_SHEET_ID = "1eFCmli9zQw-BjU2KbvLccI8e6C7-d00nzPKR5IskutQ"
ATTENDANCE_SHEET_ID = "1EJfGVlYZsv2Ue70aVwAYv20ijgm9FEq9tIhwIUwd2uc"

SITE_NAME = "ΜΟΥΣΕΙΟ"
APP_DIR = Path(__file__).resolve().parent
DEFAULT_DRIVE_PHOTOS_FOLDER = Path(r"G:\My Drive\ERGOTAXIA\Photos")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_secret(name, default=None):
    if name in os.environ and os.environ[name]:
        return os.environ[name]

    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def get_photos_folder():
    configured_folder = get_secret("PHOTOS_LOCAL_FOLDER")

    if configured_folder:
        return Path(configured_folder).expanduser()

    if DEFAULT_DRIVE_PHOTOS_FOLDER.exists():
        return DEFAULT_DRIVE_PHOTOS_FOLDER

    return APP_DIR / "photos"


PHOTOS_LOCAL_FOLDER = get_photos_folder()
PHOTOS_LOCAL_FOLDER.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Παρουσίες Εργοταξίου", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=swap');

:root {
    --page-bg: #f6f7f9;
    --panel-bg: #ffffff;
    --ink: #18202f;
    --muted: #667085;
    --line: #d9dee8;
    --green: #128a45;
    --green-dark: #0f6f39;
    --red: #d92d20;
    --red-dark: #b42318;
}

html, body, [class*="css"] {
    font-family: Inter, Arial, sans-serif;
}

.stApp {
    background:
        linear-gradient(180deg, #eef2f7 0%, var(--page-bg) 280px),
        var(--page-bg);
}

.block-container {
    max-width: 820px;
    padding-top: 2.4rem;
    padding-bottom: 2rem;
}

.app-header {
    margin: 0 0 1.25rem;
    padding: 1.35rem 1.45rem;
    color: #ffffff;
    background: linear-gradient(135deg, #18202f 0%, #25415f 100%);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    box-shadow: 0 18px 45px rgba(24, 32, 47, 0.18);
}

.app-kicker {
    margin: 0 0 0.35rem;
    color: #b9c7d8;
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0;
}

.app-title {
    margin: 0;
    font-size: clamp(2rem, 5vw, 3.2rem);
    line-height: 1.05;
    font-weight: 800;
}

.app-site {
    margin: 0.8rem 0 0;
    color: #e6edf5;
    font-size: clamp(1.05rem, 2vw, 1.35rem);
    font-weight: 700;
}

div[data-testid="stForm"] {
    padding: 1.1rem 1.1rem 1rem;
    background: var(--panel-bg);
    border: 1px solid var(--line);
    border-radius: 16px;
    box-shadow: 0 14px 35px rgba(24, 32, 47, 0.08);
}

label, div[data-testid="stTextInput"] label, div[data-testid="stCameraInput"] label {
    color: var(--ink) !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
}

div[data-testid="stTextInput"] input {
    min-height: 58px;
    color: var(--ink);
    background: #f7f8fb;
    border: 1px solid #d7dce6;
    border-radius: 12px;
    font-size: 1.15rem;
    font-weight: 700;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #426b9a;
    box-shadow: 0 0 0 3px rgba(66, 107, 154, 0.18);
}

div[data-testid="stCameraInput"] {
    margin-top: 0.6rem;
}

div[data-testid="stCameraInput"] button {
    width: 100% !important;
    min-height: 78px !important;
    color: var(--ink) !important;
    background: #ffffff !important;
    border: 2px solid #cdd5e1 !important;
    border-radius: 14px !important;
    font-size: clamp(1.25rem, 3vw, 1.8rem) !important;
    font-weight: 800 !important;
    box-shadow: none !important;
}

div[data-testid="stCameraInput"] button:hover {
    border-color: #9aa8bc !important;
    background: #f8fafc !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}

div[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
    min-height: 96px !important;
    border-radius: 16px !important;
    font-size: clamp(1.35rem, 3.2vw, 2rem) !important;
    font-weight: 800 !important;
    letter-spacing: 0 !important;
    box-shadow: 0 12px 24px rgba(24, 32, 47, 0.16) !important;
}

div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stFormSubmitButton"] button {
    background-color: var(--green) !important;
    color: #ffffff !important;
    border: 2px solid var(--green-dark) !important;
}

div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stFormSubmitButton"] button:hover {
    background-color: var(--green-dark) !important;
}

div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stFormSubmitButton"] button {
    background-color: var(--red) !important;
    color: #ffffff !important;
    border: 2px solid var(--red-dark) !important;
}

div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stFormSubmitButton"] button:hover {
    background-color: var(--red-dark) !important;
}

.success-box,
.error-box {
    margin-top: 1.2rem;
    padding: 1.25rem;
    text-align: center;
    border-radius: 16px;
    font-size: clamp(1.35rem, 3vw, 2rem);
    line-height: 1.35;
    font-weight: 800;
    box-shadow: 0 14px 35px rgba(24, 32, 47, 0.08);
}

.success-box {
    color: #064e3b;
    background-color: #dcfce7;
    border: 2px solid #22c55e;
}

.error-box {
    color: #8f1d18;
    background-color: #fee2e2;
    border: 2px solid #ef4444;
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1.1rem;
    }

    .app-header,
    div[data-testid="stForm"] {
        border-radius: 14px;
    }

    div[data-testid="stFormSubmitButton"] button {
        min-height: 86px !important;
    }
}

@media (orientation: landscape) and (max-height: 800px) {
    .block-container {
        padding-top: 3.4rem;
    }

    .app-header {
        padding: 0.95rem 1.15rem;
        margin-bottom: 0.85rem;
    }

    .app-title {
        font-size: 2.2rem;
    }

    .app-site {
        margin-top: 0.45rem;
        font-size: 1rem;
    }

    div[data-testid="stForm"] {
        padding: 0.9rem;
    }

    div[data-testid="stCameraInputWebcamStyledBox"],
    div[data-testid="stCameraInputWebcamStyledBox"] video {
        height: 185px !important;
        max-height: 185px !important;
        object-fit: cover;
    }

    div[data-testid="stCameraInput"] button {
        min-height: 64px !important;
    }

    div[data-testid="stFormSubmitButton"] button {
        min-height: 78px !important;
    }
}
</style>
""", unsafe_allow_html=True)


def normalize_code(text):
    replacements = {
        "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H",
        "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O",
        "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
        "α": "A", "β": "B", "ε": "E", "ζ": "Z", "η": "H",
        "ι": "I", "κ": "K", "μ": "M", "ν": "N", "ο": "O",
        "ρ": "P", "τ": "T", "υ": "Y", "χ": "X",
    }

    text = str(text).strip().upper()

    for greek, latin in replacements.items():
        text = text.replace(greek, latin)

    return text


@st.cache_resource
def get_sheets_client():
    service_account_json = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        service_account_info = json.loads(service_account_json)
        if "private_key" in service_account_info:
            service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    elif get_secret("gcp_service_account"):
        service_account_info = dict(get_secret("gcp_service_account"))
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    else:
        service_account_file = get_secret("GOOGLE_SERVICE_ACCOUNT_FILE", str(APP_DIR / "service_account.json"))
        creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)

    return gspread.authorize(creds)


def save_photo_local(photo, filename):
    supabase_url = get_secret("SUPABASE_URL")
    supabase_key = get_secret("SUPABASE_SERVICE_KEY")
    supabase_bucket = get_secret("SUPABASE_BUCKET", "photos")

    safe_filename = filename.replace("ΕΙΣΟΔΟΣ", "IN").replace("ΕΞΟΔΟΣ", "OUT")

    if supabase_url and supabase_key:
        upload_url = f"{supabase_url}/storage/v1/object/{supabase_bucket}/{safe_filename}"

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "image/jpeg",
            "x-upsert": "true"
        }

        response = requests.post(
            upload_url,
            headers=headers,
            data=photo.getvalue()
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Supabase upload failed: {response.text}")

        return f"{supabase_url}/storage/v1/object/public/{supabase_bucket}/{safe_filename}"

    filepath = os.path.join(PHOTOS_LOCAL_FOLDER, safe_filename)

    with open(filepath, "wb") as file:
        file.write(photo.getvalue())

    return filepath


def show_message():
    if "message" not in st.session_state:
        return

    if st.session_state.get("message_type") == "success":
        st.markdown(
            f'<div class="success-box">{st.session_state.message}</div>',
            unsafe_allow_html=True
        )
    elif st.session_state.get("message_type") == "error":
        st.markdown(
            f'<div class="error-box">{st.session_state.message}</div>',
            unsafe_allow_html=True
        )


def require_access_code():
    access_code = get_secret("APP_ACCESS_CODE")

    if not access_code or st.session_state.get("access_granted"):
        return

    with st.form(key="access_form"):
        entered_code = st.text_input("Access code", type="password")
        submitted = st.form_submit_button("Continue", use_container_width=True)

    if submitted and entered_code == access_code:
        st.session_state.access_granted = True
        st.rerun()

    if submitted:
        st.error("Wrong access code")

    st.stop()


require_access_code()

sheets_client = get_sheets_client()

workers_sheet = sheets_client.open_by_key(WORKERS_SHEET_ID).sheet1
attendance_sheet = sheets_client.open_by_key(ATTENDANCE_SHEET_ID).sheet1

workers = workers_sheet.get_all_records()

st.markdown(
    f"""
    <div class="app-header">
        <p class="app-kicker">Σύστημα παρουσιών</p>
        <h1 class="app-title">Παρουσίες Εργοταξίου</h1>
        <p class="app-site">Έργο: {SITE_NAME}</p>
    </div>
    """,
    unsafe_allow_html=True
)


def find_worker(code):
    normalized_code = normalize_code(code)

    for worker in workers:
        if normalize_code(worker.get("Code", "")) != normalized_code:
            continue

        status_value = None
        for field in ("Active", "IsActive", "Status", "Enabled"):
            if field in worker and str(worker.get(field, "")).strip():
                status_value = normalize_code(worker.get(field))
                break

        if status_value in {"0", "FALSE", "NO", "N", "OFF", "INACTIVE", "DISABLED", "ANENERGOS"}:
            continue

        return worker

    return None


def get_last_action_today(worker_code):
    today = datetime.now(ZoneInfo("Europe/Athens"))
    today_str = today.strftime("%d/%m/%Y")
    today_date = today.date()
    records = attendance_sheet.get_all_records()

    worker_records_today = []

    for record in records:
        record_date = record.get("Date", "")

        if isinstance(record_date, datetime):
            is_today = record_date.date() == today_date
        else:
            is_today = str(record_date).strip() == today_str

        if not is_today:
            continue

        if normalize_code(record.get("Code", "")) == normalize_code(worker_code):
            worker_records_today.append(record)

    if not worker_records_today:
        return None

    return worker_records_today[-1].get("Action", "")


def save_attendance(worker, action, photo):
    now = datetime.now(ZoneInfo("Europe/Athens"))

    filename = f"{worker['Code']}_{now.strftime('%Y%m%d_%H%M%S')}_{action}.jpg"
    photo_path = save_photo_local(photo, filename)

    row = [
        now.strftime("%d/%m/%Y"),
        now.strftime("%H:%M:%S"),
        worker["Code"],
        worker["FirstName"],
        worker["LastName"],
        worker["Specialty"],
        worker["DailyWage"],
        SITE_NAME,
        action,
        photo_path
    ]

    attendance_sheet.append_row(row)

    st.session_state.message = (
        f"✓ ΚΑΤΑΧΩΡΗΘΗΚΕ<br><br>"
        f"{action}<br>"
        f"{worker['FirstName']} {worker['LastName']}<br>"
        f"{now.strftime('%H:%M:%S')}"
    )
    st.session_state.message_type = "success"


if "is_submitting" not in st.session_state:
    st.session_state.is_submitting = False


with st.form(key="attendance_form_main", clear_on_submit=True):
    code_input = st.text_input(
        "Κωδικός εργάτη",
        placeholder="π.χ. A001",
        key="code_input_main"
    )

    photo = st.camera_input(
        "Φωτογραφία παρουσίας",
        key="photo_input_main"
    )

    col1, col2 = st.columns(2)

    with col1:
        entry_pressed = st.form_submit_button(
            "ΕΙΣΟΔΟΣ",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_submitting
        )


    with col2:
        exit_pressed = st.form_submit_button(
            "ΕΞΟΔΟΣ",
            type="secondary",
            use_container_width=True,
            disabled=st.session_state.is_submitting
        )

    if entry_pressed or exit_pressed:
        if st.session_state.is_submitting:
            st.stop()

        st.session_state.is_submitting = True

        try:
            worker = find_worker(code_input)

            if not worker:
                st.session_state.message = "ΛΑΘΟΣ Ή ΑΝΕΝΕΡΓΟΣ ΚΩΔΙΚΟΣ"
                st.session_state.message_type = "error"

            elif photo is None:
                st.session_state.message = "ΠΡΕΠΕΙ ΝΑ ΒΓΕΙ ΦΩΤΟΓΡΑΦΙΑ"
                st.session_state.message_type = "error"

            else:
                action = "ΕΙΣΟΔΟΣ" if entry_pressed else "ΕΞΟΔΟΣ"
                last_action = get_last_action_today(worker["Code"])

                if last_action == action:
                    st.session_state.message = f"Ο ΕΡΓΑΖΟΜΕΝΟΣ ΕΧΕΙ ΗΔΗ ΚΑΝΕΙ {action}"
                    st.session_state.message_type = "error"
                else:
                    last_action = get_last_action_today(worker["Code"])

                    if last_action == action:
                        st.session_state.message = f"Ο ΕΡΓΑΖΟΜΕΝΟΣ ΕΧΕΙ ΗΔΗ ΚΑΝΕΙ {action}"
                        st.session_state.message_type = "error"
                    else:
                        save_attendance(worker, action, photo)
        finally:
            st.session_state.is_submitting = False

show_message()
