# Build Guide

## What you will need

| Tool | Where to get |
|------|-------------|
| Python 3.10+ | https://python.org/downloads - tick **Add to PATH** |
| Inno Setup | https://jrsoftware.org/isinfo.php |
| UPX (optional, smaller exe) | https://upx.github.io - add to PATH |

---

## Step 1 - Build the exe

Put all these files in the same folder:
```
wiz_control.py
wiz_control.spec
build.bat
requirements.txt
```

Double-click **build.bat**. It will:
1. Check Python is installed
2. Auto-install `customtkinter`, `Pillow`, `pystray`, `PyInstaller` if missing
3. Run PyInstaller using the spec file
4. Output: `dist\WizControl.exe`

exe now fully self-contained no Python or pip needed on the end user's machine

---

## Step 2 - Create the installer (optional)

1. Install **Inno Setup**
2. Open `wiz_control_installer.iss` in Inno Setup Compiler
3. Edit the `#define AppURL` line to your actual GitHub/download URL
4. Press **Build → Compile** (or Ctrl+F9)
5. Output: `installer_output\WizControl_Setup_v4.2.exe`

---


## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: customtkinter` at runtime | Add `customtkinter` to `hiddenimports` in spec |
| Blank window on launch | Make sure `console=False` is set in spec |
| Antivirus flags the exe | Normal for PyInstaller single-file builds. Submit to AV vendor for whitelisting, or use `--onedir` mode instead |
| `UPX` not found warning | Either install UPX and add to PATH, or set `upx=False` in the spec |
