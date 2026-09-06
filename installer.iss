; Audio Splitter Pro - Windows Installer Script
; Build this with Inno Setup (free): https://jrsoftware.org/isdl.php
;
; HOW TO USE:
; 1. First run build_exe.bat to create dist\AudioSplitterPro.exe
; 2. Install Inno Setup from the link above
; 3. Open this file (installer.iss) with Inno Setup
; 4. Click Build > Compile
; 5. You'll get "AudioSplitterPro_Setup.exe" - THIS is what you double-click
;    to install the app properly (Start Menu entry + Desktop icon + Uninstaller)

#define MyAppName "Audio Splitter Pro"
#define MyAppVersion "1.0"
#define MyAppExeName "AudioSplitterPro.exe"

[Setup]
AppId={{B8F1C1A0-1234-4E56-9ABC-AUDIOSPLIT001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=AudioSplitterPro_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Uses a simple color scheme; app itself is dark-themed
SetupIconFile=
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Uninstall shortcut in Start Menu
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
; Optional Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
