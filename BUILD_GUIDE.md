# Build Guide

Complete guide for building WizControl from source.

---

## Prerequisites

### Required Software

**Python 3.10 or higher**

* [https://python.org/downloads](https://python.org/downloads)
* Enable “Add Python to PATH”
* Verify:

```
python --version
```


**Inno Setup**

* [https://jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)

---



# Option 1: Automated Build

```
git clone https://github.com/asttttt/wiz-control.git
cd wiz-control
build.bat
```

**Output:**

```
dist\WizControl.exe
```

---

# Option 2: Manual Build

```
pip install -r requirements.txt
pyinstaller wiz_control.spec --noconfirm
```

---

# Building the Installer

1. Open `wiz_control_installer.iss` in Inno Setup
2. Click **Compile**
3. Output:

```
installer_output\WizControl_Setup_v1.2.exe
```

---

## Project Structure

```
wiz-control/
├── wiz_control.py
├── wiz_control.spec
├── wiz_control_installer.iss
├── build.bat
├── requirements.txt
│
├── dist/
│   └── WizControl.exe
│
├── build/
│
└── installer_output/
    └── WizControl_Setup_v1.2.exe
```

---

# How It Works

### PyInstaller

* Reads `.py` and `.spec`
* Bundles Python runtime and dependencies
* Outputs standalone `.exe`

### Bundled Components

* Python runtime
* customtkinter
* Pillow
* pystray
* standard libraries

---

## User Data

* Stored at:

```
%APPDATA%\WizControl\wiz_slots.json
```


### Commit to Repo

* `.py`, `.spec`, `.iss`
* `requirements.txt`
* `build.bat`
* documentation files

---

