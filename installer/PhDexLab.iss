#ifndef AppVersion
#define AppVersion "0.11.0"
#endif
#ifndef ApplicationDir
#define ApplicationDir "..\Application"
#endif
#ifndef DestinationDir
#define DestinationDir "..\.."
#endif
[Setup]
AppId={code:InstallAppId}
AppName=PhDexLab
AppVersion={#AppVersion}
AppPublisher=RpastranaE
AppPublisherURL=https://github.com/RpastranaE/PhDexLab
AppSupportURL=https://github.com/RpastranaE/PhDexLab/issues
DefaultDirName={localappdata}\Programs\PhDexLab
DefaultGroupName=PhDexLab
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#DestinationDir}
OutputBaseFilename=PhDexLab-Setup-{#AppVersion}
SetupIconFile=..\phdexlab\assets\phdexlab.ico
UninstallDisplayIcon={app}\Application\PhDexLab.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LanguageDetectionMethod=none
UsePreviousLanguage=no
CloseApplications=yes
RestartApplications=no
LicenseFile=..\LICENSE
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
[Files]
Source: "{#ApplicationDir}\*"; DestDir: "{app}\Application"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{code:MenuDirectory}\PhDexLab"; Filename: "{app}\Application\PhDexLab.exe"; WorkingDir: "{app}"
Name: "{code:DesktopDirectory}\PhDexLab"; Filename: "{app}\Application\PhDexLab.exe"; WorkingDir: "{app}"; Tasks: desktopicon
[Run]
Filename: "{app}\Application\PhDexLab.exe"; Description: "{cm:LaunchProgram,PhDexLab}"; Flags: nowait postinstall skipifsilent
[Code]
function InstallAppId(Param: String): String;
begin
  { Isolated verification can use its own uninstall registration. }
  Result := ExpandConstant('{param:InstallId|}');
  if Result = '' then Result := '{6FCA38DF-F22F-4E6C-88BB-637ECF412030}';
end;
function MenuDirectory(Param: String): String;
begin
  Result := ExpandConstant('{param:MenuDir|{group}}');
end;
function DesktopDirectory(Param: String): String;
begin
  { Optional override supports isolated installation verification. }
  Result := ExpandConstant('{param:DesktopDir|{autodesktop}}');
end;
