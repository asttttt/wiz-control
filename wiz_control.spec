# wiz_control.spec
# Run with:  pyinstaller wiz_control.spec

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Pull in all customtkinter assets (themes, fonts, images)
ctk_datas    = collect_data_files('customtkinter', include_py_files=False)
pillow_datas = collect_data_files('PIL')

a = Analysis(
    ['wiz_control.py'],
    pathex=['.'],
    binaries=[],
    datas=ctk_datas + pillow_datas,
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageTk',
        'pystray',
        'pystray._win32',
        'colorsys',
        'socket',
        'json',
        'threading',
        'http.server',
        'socketserver',
        'urllib.parse',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest', 'xmlrpc', 'lib2to3'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WizControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='wiz_control.ico',  # uncomment and add an .ico file to use it if u want
)
