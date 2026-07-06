import requests
import json
import os
import hashlib
import html
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import cv2
    import numpy as np
    QR_SCANNER_AVAILABLE = True
except Exception:
    cv2 = None
    np = None
    QR_SCANNER_AVAILABLE = False

WORKERS_SHEET_ID = "1eFCmli9zQw-BjU2KbvLccI8e6C7-d00nzPKR5IskutQ"
ATTENDANCE_SHEET_ID = "1EJfGVlYZsv2Ue70aVwAYv20ijgm9FEq9tIhwIUwd2uc"

SITE_NAME = "ΜΟΥΣΕΙΟ"
APP_DIR = Path(__file__).resolve().parent
DEFAULT_DRIVE_PHOTOS_FOLDER = Path(r"G:\My Drive\ERGOTAXIA\Photos")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SUCCESS_BEEP_WAV_B64 = (
    "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"
)

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


def decode_qr_worker_code(image_file):
    if not QR_SCANNER_AVAILABLE or image_file is None:
        return None

    image_bytes = image_file.getvalue()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        return None

    detector = cv2.QRCodeDetector()
    decoded_text, _, _ = detector.detectAndDecode(image)
    decoded_text = normalize_code(decoded_text)

    return decoded_text if decoded_text else None


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


def queue_fullscreen_feedback(kind, title, lines, beep=False):
    st.session_state.feedback_counter = st.session_state.get("feedback_counter", 0) + 1
    st.session_state.fullscreen_feedback = {
        "id": st.session_state.feedback_counter,
        "kind": kind,
        "title": title,
        "lines": list(lines),
        "beep": beep,
    }


def render_fullscreen_feedback():
    feedback = st.session_state.get("fullscreen_feedback")
    if not feedback:
        return

    rendered_id = st.session_state.get("fullscreen_feedback_rendered_id")
    if rendered_id == feedback["id"]:
        return

    if feedback["kind"] == "success":
        panel_class = "fs-success"
        badge = "✓"
        show_audio = feedback.get("beep", False)
    else:
        panel_class = "fs-error"
        badge = "!"
        show_audio = False

    lines_html = "".join(
        f'<div class="fs-line">{html.escape(str(line))}</div>'
        for line in feedback.get("lines", [])
        if str(line).strip()
    )

    audio_html = ""
    if show_audio:
        audio_html = (
            f'<audio autoplay playsinline preload="auto" style="display:none">'
            f'<source src="data:audio/wav;base64,{SUCCESS_BEEP_WAV_B64}" type="audio/wav">'
            f"</audio>"
        )

    st.markdown(
        f"""
        <style>
        .fs-overlay {{
            position: fixed;
            inset: 0;
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(8, 15, 28, 0.72);
            animation: fsFadeOut 2s ease forwards;
        }}

        .fs-panel {{
            width: min(92vw, 980px);
            min-height: min(82vh, 760px);
            border-radius: 28px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 2rem;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.35);
            transform: scale(1);
            animation: fsPulse 2s ease forwards;
        }}

        .fs-success {{
            color: #ecfdf5;
            background: linear-gradient(135deg, #0f8a44 0%, #156f3a 100%);
            border: 4px solid rgba(255, 255, 255, 0.18);
        }}

        .fs-error {{
            color: #fff7ed;
            background: linear-gradient(135deg, #c2410c 0%, #b91c1c 100%);
            border: 4px solid rgba(255, 255, 255, 0.18);
        }}

        .fs-badge {{
            font-size: clamp(5rem, 18vw, 10rem);
            line-height: 1;
            font-weight: 900;
            margin-bottom: 0.4rem;
        }}

        .fs-title {{
            font-size: clamp(2rem, 6vw, 4.5rem);
            font-weight: 900;
            letter-spacing: 0.01em;
            line-height: 1.05;
            margin-bottom: 1rem;
        }}

        .fs-line {{
            font-size: clamp(1.5rem, 4vw, 2.6rem);
            font-weight: 800;
            line-height: 1.2;
            margin-top: 0.35rem;
        }}

        @keyframes fsFadeOut {{
            0% {{ opacity: 1; }}
            84% {{ opacity: 1; }}
            100% {{ opacity: 0; visibility: hidden; }}
        }}

        @keyframes fsPulse {{
            0% {{ transform: scale(0.98); }}
            25% {{ transform: scale(1); }}
            100% {{ transform: scale(1); }}
        }}
        </style>
        <div class="fs-overlay">
            <div class="fs-panel {panel_class}">
                <div class="fs-badge">{badge}</div>
                <div class="fs-title">{html.escape(str(feedback.get("title", "")))}</div>
                {lines_html}
            </div>
        </div>
        {audio_html}
        """,
        unsafe_allow_html=True
    )

    st.session_state.fullscreen_feedback_rendered_id = feedback["id"]


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



render_fullscreen_feedback()

def _is_active_worker(worker):
    status_value = None

    for field in ("Active", "IsActive", "Status", "Enabled"):
        if field in worker and str(worker.get(field, "")).strip():
            status_value = normalize_code(worker.get(field))
            break

    return status_value not in {
        "0", "FALSE", "NO", "N", "OFF", "INACTIVE", "DISABLED", "ANENERGOS"
    }


def get_today_dashboard():
    today = datetime.now(ZoneInfo("Europe/Athens"))
    today_str = today.strftime("%d/%m/%Y")
    records = attendance_sheet.get_all_records()

    total_active = 0
    present_count = 0
    left_count = 0

    for worker in workers:
        if not _is_active_worker(worker):
            continue

        total_active += 1
        normalized_worker_code = normalize_code(worker.get("Code", ""))

        worker_records_today = [
            record
            for record in records
            if str(record.get("Date", "")).strip() == today_str
            and normalize_code(record.get("Code", "")) == normalized_worker_code
        ]

        if not worker_records_today:
            continue

        latest_action = worker_records_today[-1].get("Action", "")

        if latest_action == "ΕΙΣΟΔΟΣ":
            present_count += 1
        elif latest_action == "ΕΞΟΔΟΣ":
            left_count += 1

    absent_count = total_active - present_count - left_count

    return total_active, present_count, left_count, absent_count


dashboard_total_active, dashboard_present_count, dashboard_left_count, dashboard_absent_count = get_today_dashboard()

dashboard_col1, dashboard_col2, dashboard_col3, dashboard_col4 = st.columns(4)

dashboard_col1.metric("Ενεργοί", dashboard_total_active)
dashboard_col2.metric("Παρόντες", dashboard_present_count)
dashboard_col3.metric("Έφυγαν", dashboard_left_count)
dashboard_col4.metric("Άποντες", dashboard_absent_count)

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
        f"? ????????????<br><br>"
        f"{action}<br>"
        f"{worker['FirstName']} {worker['LastName']}<br>"
        f"{now.strftime('%H:%M:%S')}"
    )
    st.session_state.message_type = "success"
    queue_fullscreen_feedback(
        "success",
        f"???????? {action}",
        [
            f"{worker['FirstName']} {worker['LastName']}",
            now.strftime("%H:%M:%S"),
        ],
        beep=True,
    )


if "is_submitting" not in st.session_state:
    st.session_state.is_submitting = False

if "qr_scan_nonce" not in st.session_state:
    st.session_state.qr_scan_nonce = 0

if "qr_scanned_code" not in st.session_state:
    st.session_state.qr_scanned_code = ""

if "qr_scan_digest" not in st.session_state:
    st.session_state.qr_scan_digest = ""


def render_disabled_action_button(label):
    st.markdown(
        f"""
        <button disabled style="
            width: 100%;
            min-height: 96px;
            border-radius: 16px;
            font-size: clamp(1.35rem, 3.2vw, 2rem);
            font-weight: 800;
            letter-spacing: 0;
            color: #8b95a7;
            background: #e5e7eb;
            border: 2px solid #cbd5e1;
            box-shadow: 0 12px 24px rgba(24, 32, 47, 0.08);
            cursor: not-allowed;
        ">{label}</button>
        """,
        unsafe_allow_html=True
    )


code_input = st.text_input(
    "Κωδικός εργάτη",
    placeholder="π.χ. A001",
    key="code_input_main"
)

st.markdown("**QR scan (optional)**")
qr_scan_image = st.camera_input(
    "Scan a QR code containing the worker code",
    key=f"qr_scan_input_{st.session_state.qr_scan_nonce}"
)

if qr_scan_image is not None:
    qr_scan_digest = hashlib.sha1(qr_scan_image.getvalue()).hexdigest()

    if qr_scan_digest != st.session_state.qr_scan_digest:
        st.session_state.qr_scan_digest = qr_scan_digest
        scanned_qr_code = decode_qr_worker_code(qr_scan_image)

        if scanned_qr_code:
            st.session_state.qr_scanned_code = scanned_qr_code
        else:
            st.session_state.qr_scanned_code = ""

if st.session_state.qr_scanned_code:
    st.success(f"QR code ready: {st.session_state.qr_scanned_code}")
    if st.button("Clear QR scan", key="clear_qr_scan"):
        st.session_state.qr_scanned_code = ""
        st.session_state.qr_scan_digest = ""
        st.session_state.qr_scan_nonce += 1
        st.rerun()
elif not QR_SCANNER_AVAILABLE:
    st.info("QR scanning is unavailable because OpenCV is not installed.")

effective_code = st.session_state.qr_scanned_code or code_input
worker = find_worker(effective_code)
last_action = get_last_action_today(worker["Code"]) if worker else None

allow_entry = False
allow_exit = False
next_action = None

if worker:
    if last_action is None:
        allow_entry = True
        next_action = "ΕΙΣΟΔΟΣ"
    elif last_action == "ΕΙΣΟΔΟΣ":
        allow_exit = True
        next_action = "ΕΞΟΔΟΣ"
    elif last_action == "ΕΞΟΔΟΣ":
        allow_entry = True
        next_action = "ΕΙΣΟΔΟΣ"

with st.form(key="attendance_form_main", clear_on_submit=True):
    photo = st.camera_input(
        "Φωτογραφία παρουσίας",
        key="photo_input_main"
    )

    col1, col2 = st.columns(2)

    with col1:
        if allow_entry:
            entry_pressed = st.form_submit_button(
                "ΕΙΣΟΔΟΣ",
                type="primary",
                use_container_width=True
            )
        else:
            entry_pressed = False
            render_disabled_action_button("✓ ΟΛΟΚΛΗΡΩΘΗΚΕ")

    with col2:
        if allow_exit:
            exit_pressed = st.form_submit_button(
                "ΕΞΟΔΟΣ",
                type="secondary",
                use_container_width=True
            )
        else:
            exit_pressed = False
            render_disabled_action_button("✓ ΟΛΟΚΛΗΡΩΘΗΚΕ")

    if entry_pressed or exit_pressed:
        if st.session_state.is_submitting:
            st.stop()

        st.session_state.is_submitting = True
        should_rerun = False

        try:
            if not worker:
                error_message = "????? ? ????????? ???????"
                st.session_state.message = error_message
                st.session_state.message_type = "error"
                queue_fullscreen_feedback("error", "??????", [error_message])
                should_rerun = True

            elif photo is None:
                error_message = "?????? ?? ???? ??????????"
                st.session_state.message = error_message
                st.session_state.message_type = "error"
                queue_fullscreen_feedback("error", "??????", [error_message])
                should_rerun = True

            else:
                action = "???????" if entry_pressed else "??????"
                last_action = get_last_action_today(worker["Code"])

                if last_action == action:
                    error_message = f"? ??????????? ???? ??? ????? {action}"
                    st.session_state.message = error_message
                    st.session_state.message_type = "error"
                    queue_fullscreen_feedback("error", "??????", [error_message])
                    should_rerun = True
                else:
                    last_action = get_last_action_today(worker["Code"])

                    if last_action == action:
                        error_message = f"? ??????????? ???? ??? ????? {action}"
                        st.session_state.message = error_message
                        st.session_state.message_type = "error"
                        queue_fullscreen_feedback("error", "??????", [error_message])
                        should_rerun = True
                    else:
                        try:
                            save_attendance(worker, action, photo)
                        except Exception:
                            error_message = "?????? ???? ??? ??????????"
                            st.session_state.message = error_message
                            st.session_state.message_type = "error"
                            queue_fullscreen_feedback("error", "??????", [error_message])
                            should_rerun = True
                        else:
                            st.session_state.qr_scanned_code = ""
                            st.session_state.qr_scan_digest = ""
                            st.session_state.qr_scan_nonce += 1
                        should_rerun = True
        finally:
            st.session_state.is_submitting = False

        if should_rerun:
            st.rerun()

show_message()
