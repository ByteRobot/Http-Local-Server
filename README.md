# Local Server 

A simple, fast desktop GUI to share any local folder over HTTP on your LAN.

---
<img width="761" height="503" alt="img" src="https://github.com/user-attachments/assets/ba893b48-8182-45c2-84af-e0d685298623" />

## What Is This?

PocketServer is a small PyQt5 application that wraps Python’s built‑in `http.server` in a friendly window.  
Pick a folder, click Start, and instantly open it from other devices on the same network.

---

## Why Use It?

- No terminal commands
- Start / Stop server instantly
- Share with phones (QR code)
- Copy or open URLs in one click
- See requests + bytes served
- Dark / Light theme toggle
- Remembers your last settings

---

## Features (Plain & Simple)

- Serve any directory (read‑only)
- Bind to all interfaces (0.0.0.0) or just localhost
- Auto-find a free port
- Live log with filter (regex or text)
- Uptime, request count, bytes sent
- Restart without closing the app
- Immediate stop (no hanging)
- Optional QR code for quick mobile access
- Settings saved (theme, port, directory, autostart)

---

## Technologies / Libraries

| Purpose        | Library            |
| -------------- | ------------------ |
| GUI            | PyQt5              |
| HTTP Serving   | Python stdlib (`http.server`, `socketserver`) |
| QR Codes (opt) | `qrcode` (Pillow dep) |
| Styling / Anim | Qt stylesheets + `QPropertyAnimation` |

---

## Installation

```bash
# (Recommended) create a virtual environment
python -m venv .venv
# Activate:
#   Windows: .venv\Scripts\activate
#   macOS/Linux: source .venv/bin/activate

# Install required libs
pip install PyQt5

# (Optional) for QR code feature
pip install qrcode
```

---

## Run

```bash
python server4.py
```

(Or double‑click the file if your OS associates .py with Python.)

---

## Basic Use

1. Launch app  
2. Pick/Browse directory  
3. (Optional) choose port or click “Auto Port”  
4. (Optional) uncheck “All Interfaces” to limit to `127.0.0.1`  
5. Click Start Server  
6. Click a URL to open it, right‑click to copy  
7. Use QR Code (if enabled) on mobile  
8. Click Stop when done  

---

## Settings Saved

- Port
- Last directory (if enabled)
- Theme (dark/light)
- Autostart toggle

You can disable “Remember last directory” in Settings.

---

## Limitations

- Read‑only (no uploads)
- No authentication
- Not HTTPS (local / trusted network use only)
- Not meant for Internet exposure

---

## Uninstall / Clean Up

Just delete `server4.py` and (optionally) remove the virtual environment:
```bash
deactivate
rm -rf .venv
```

---

## Optional: Build an Executable

```bash
pip install pyinstaller
pyinstaller --windowed --name PocketServer server4.py
```

---

## Safety Note

Do not serve sensitive folders while bound to `0.0.0.0` on untrusted networks.

---

## Roadmap (Maybe Later)

- Drag & drop folder
- Basic auth
- Uploads
- HTTPS toggle
- System tray mode

---

