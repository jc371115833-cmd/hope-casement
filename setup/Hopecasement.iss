; Non-commercial use only

#define MyAppName "HopeCasement"
#define MyAppVersion ReadIni(SourcePath + "\..\pyproject.toml", "project", "version", "")
#if MyAppVersion == ""
  #error "Missing project.version in pyproject.toml"
#endif
#define MyAppPublisher "KingKing"
#define MyAppExeName "HopeCasement.exe"

[Setup]
AppId={{2FB42E98-50ED-4FEE-8024-3B20F66DFF40}
; Display name is localized; the install folder stays the ASCII "HopeCasement".
AppName={cm:AppDisplayName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoDescription={#MyAppName} Setup
DefaultDirName={localappdata}\{#MyAppName}
UninstallDisplayName={cm:AppDisplayName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#SourcePath}
OutputBaseFilename=HopeCasement
SetupIconFile={#SourcePath}\..\src\hopecasement\ui\hopecasement.ico
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[CustomMessages]
english.AppDisplayName=HopeCasement
chinesesimplified.AppDisplayName=来日窗笺

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourcePath}\..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{cm:AppDisplayName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{cm:AppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "HopeCasement"; Flags: uninsdeletevalue
; Record the chosen language so the app launches in the same one.
Root: HKCU; Subkey: "Software\HopeCasement"; ValueType: string; ValueName: "Language"; ValueData: "zh"; Languages: chinesesimplified; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\HopeCasement"; ValueType: string; ValueName: "Language"; ValueData: "en"; Languages: english; Flags: uninsdeletekey

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/delete /tn \HopeCasement\ChangeOnInterval /f"; Flags: runhidden; RunOnceId: "DelTaskInterval"
Filename: "schtasks.exe"; Parameters: "/delete /tn \HopeCasement\ChangeAtTime /f"; Flags: runhidden; RunOnceId: "DelTaskDaily"

; Remove user data created at runtime so uninstall leaves no traces.
[UninstallDelete]
Type: filesandordirs; Name: "{app}\backgrounds"
Type: filesandordirs; Name: "{app}\history"
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\quotes.txt"
Type: files; Name: "{app}\current_wallpaper.png"
Type: files; Name: "{app}\state.json"
Type: files; Name: "{app}\error.log"
Type: dirifempty; Name: "{app}"

