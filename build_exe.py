import importlib.util
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_DIR / "build"
DIST_DIR = PROJECT_DIR / "dist"
EXE_NAME = "ErgotaxioAttendance"
LAUNCHER = BUILD_DIR / "streamlit_exe_launcher.py"


LAUNCHER_CODE = r'''
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def resource_path(*parts):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)
    return Path(__file__).resolve().parent.joinpath(*parts)


def wait_for_server(host, port, timeout_seconds=20):
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.25)

    return False


def open_browser_when_ready(host, port):
    if wait_for_server(host, port):
        webbrowser.open(f"http://{host}:{port}")


def main():
    app_path = resource_path("app.py")
    config_dir = resource_path(".streamlit")
    exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path.cwd()
    host = os.environ.get("ERGOTAXIO_HOST", "0.0.0.0")
    browser_host = "127.0.0.1"
    port = os.environ.get("ERGOTAXIO_PORT", "8501")

    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", host)
    os.environ.setdefault("STREAMLIT_SERVER_PORT", port)
    os.environ.setdefault("PHOTOS_LOCAL_FOLDER", str(exe_dir / "photos"))

    if config_dir.exists():
        os.environ.setdefault("STREAMLIT_GLOBAL_CONFIG_DIR", str(config_dir))

    threading.Thread(
        target=open_browser_when_ready,
        args=(browser_host, int(port)),
        daemon=True,
    ).start()

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        port,
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
'''


def require_pyinstaller():
    if importlib.util.find_spec("PyInstaller") is not None:
        return

    print("PyInstaller is not installed in this Python environment.")
    print("Installing it now with pip...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def add_data_args():
    data_items = [
        (PROJECT_DIR / "app.py", "."),
        (PROJECT_DIR / ".streamlit", ".streamlit"),
    ]

    service_account = PROJECT_DIR / "service_account.json"
    if service_account.exists():
        data_items.append((service_account, "."))

    photos_dir = PROJECT_DIR / "photos"
    if photos_dir.exists():
        data_items.append((photos_dir, "photos"))

    args = []
    separator = ";" if sys.platform.startswith("win") else ":"

    for source, destination in data_items:
        if source.exists():
            args.extend(["--add-data", f"{source}{separator}{destination}"])

    return args


def main():
    require_pyinstaller()

    BUILD_DIR.mkdir(exist_ok=True)
    LAUNCHER.write_text(LAUNCHER_CODE, encoding="utf-8")

    import PyInstaller.__main__

    args = [
        str(LAUNCHER),
        "--name",
        EXE_NAME,
        "--onefile",
        "--clean",
        "--noconfirm",
        "--collect-all",
        "streamlit",
        "--collect-all",
        "gspread",
        "--collect-all",
        "google.oauth2",
        "--hidden-import",
        "streamlit.web.cli",
        "--hidden-import",
        "google.oauth2.service_account",
        "--hidden-import",
        "gspread",
        *add_data_args(),
    ]

    PyInstaller.__main__.run(args)

    exe_suffix = ".exe" if sys.platform.startswith("win") else ""
    exe_path = DIST_DIR / f"{EXE_NAME}{exe_suffix}"
    print()
    print(f"Done. Your single-file executable is here:")
    print(exe_path)


if __name__ == "__main__":
    main()
