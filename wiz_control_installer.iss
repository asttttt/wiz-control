; WizControl Inno Setup Script
; Run this in Inno Setup Compiler AFTER build.bat has produced dist\WizControl.exe
; Download Inno Setup: https://jrsoftware.org/isinfo.php
;
; IMPORTANT NOTES:
; ────────────────────────────────────────────────────────────────────────────
; 1. This installer packages the PRE-BUILT exe from dist\WizControl.exe
; 2. The exe is STANDALONE — Python/libraries are already bundled by PyInstaller
; 3. End users DO NOT need Python installed
; 4. User IPs are saved to %APPDATA%\WizControl\wiz_slots.json AFTER installation
; 5. User IPs are NEVER included in the exe or installer
; ────────────────────────────────────────────────────────────────────────────
;
; BUILD PREREQUISITES (for developers building the exe):
; • Python 3.10+   → https://python.org/downloads (add to PATH)
; • Run build.bat  → Installs dependencies and builds dist\WizControl.exe
;
; INSTALLER PREREQUISITES (for creating the installer):
; • Inno Setup    → https://jrsoftware.org/isinfo.php
; • dist\WizControl.exe must exist (created by build.bat)
; ────────────────────────────────────────────────────────────────────────────

#define AppName      "WizControl"
#define AppVersion   "4.3"
#define AppPublisher "Arif"
#define AppExeName   "WizControl.exe"
#define AppURL       "https://github.com/asttttt/wiz-control"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=WizControl_Setup_v{#AppVersion}
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Appearance
WizardStyle=modern
; Require admin only if needed, otherwise per-user
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";    GroupDescription: "Additional icons:"
Name: "startupentry";   Description: "Launch WizControl at &startup"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; The compiled exe from dist\ folder
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";              Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";   Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}";       Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";       Filename: "{app}\{#AppExeName}"; Tasks: startupentry

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the saved config on uninstall (optional — comment out to keep settings)
; Type: filesandordirs; Name: "{userappdata}\WizControl"
