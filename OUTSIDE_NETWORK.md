# Running Outside The Local Network

The app is configured to listen on all network interfaces through `.streamlit/config.toml`.

## Use On An Android Tablet

The Android tablet does not run the Windows `.exe` directly. Run the app on the
Windows PC, then open it from the tablet browser.

1. Start the app on the PC:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

or run:

```powershell
dist\ErgotaxioAttendance.exe
```

2. On the Android tablet, open Chrome and go to:

```text
http://192.168.1.202:8501
```

3. In Chrome, tap the menu and choose **Add to Home screen**. This gives the
tablet an app-like icon for attendance entry.

The PC must stay on and connected to the same network while the tablet is using
the app. If the camera does not open from the tablet, use the HTTPS tunnel
option below.

## Run From The PC

Run it with:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Local URL:

```text
http://127.0.0.1:8501
```

LAN URL on this machine:

```text
http://192.168.1.202:8501
```

For phones/tablets outside the local network, use an HTTPS public URL. Browser camera access does not work reliably over plain HTTP public IP addresses.

Good options are:

```powershell
cloudflared tunnel --url http://localhost:8501
```

or:

```powershell
ngrok http 8501
```

When exposing the app publicly, set an access code in `.streamlit/secrets.toml`:

```toml
APP_ACCESS_CODE = "your-private-code"
```

Optional deployment settings:

```toml
PHOTOS_LOCAL_FOLDER = "G:\\My Drive\\ERGOTAXIA\\Photos"
GOOGLE_SERVICE_ACCOUNT_FILE = "service_account.json"
```

If running on a hosted server, use `GOOGLE_SERVICE_ACCOUNT_JSON` instead of uploading a loose credential file.
