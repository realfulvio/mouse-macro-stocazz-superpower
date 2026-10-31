; Programma di installazione Windows (Inno Setup 6), per utente: niente
; permessi di amministratore, niente servizi, niente protezioni toccate.
; Lo compila build_windows_installer.py dalla stessa cartella usata per lo ZIP:
;   ISCC /DAppVersion=X.Y.Z /DSource=<cartella del pacchetto> /DOutputDir=<dist>
; Installa in %LOCALAPPDATA%\Programs\Mouse Macro Stocazz Superpower, crea il
; collegamento nel menu Start e (casella attiva di default) sul desktop.
; I collegamenti avviano direttamente il pythonw.exe firmato PSF.
; L'aggiornamento dal programma installato scarica il nuovo setup, ne verifica
; lo SHA-256 e lo esegue con /SILENT: stessa cartella, stessi collegamenti.

#ifndef AppVersion
  #error Passa /DAppVersion=X.Y.Z
#endif
#ifndef Source
  #error Passa /DSource=<cartella del pacchetto>
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

#define AppName "Mouse Macro Stocazz Superpower"
#define AppMutex "Local\MouseMacroSuperpower017"
#define Repo "https://github.com/realfulvio/mouse-macro-stocazz-superpower"

[Setup]
AppId={{6D3C9A41-2F7B-4E58-9B1D-8A0E5C7F3B21}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=hcok
AppPublisherURL={#Repo}
AppSupportURL={#Repo}/issues
AppUpdatesURL={#Repo}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
DisableReadyPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename=MouseMacroStocazzSuperpower-Setup-v{#AppVersion}
SetupIconFile={#Source}\app\assets\icon.ico
UninstallDisplayIcon={app}\app\assets\icon.ico
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany=hcok
VersionInfoDescription={#AppName} - installazione
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}.0
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no
ShowLanguageDialog=auto

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
it.AppRunning=Mouse Macro è aperto. Chiudilo (pulsante × del pannello) e premi Riprova.
en.AppRunning=Mouse Macro is running. Close it (× on the panel) and press Retry.
it.LaunchAfter=Avvia Mouse Macro
en.LaunchAfter=Start Mouse Macro
it.ShortcutComment=Registra e riproduci le macro del mouse
en.ShortcutComment=Record and replay mouse macros

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; Un aggiornamento sostituisce interamente programma e runtime: niente file orfani.
Type: filesandordirs; Name: "{app}\app"
Type: filesandordirs; Name: "{app}\runtime"

[Files]
Source: "{#Source}\*"; DestDir: "{app}"; Excludes: "Mouse Macro v*.exe,Mouse Macro v*.cmd"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\runtime\pythonw.exe"; Parameters: "-B ""{app}\app\windows_main.py"""; WorkingDir: "{app}"; IconFilename: "{app}\app\assets\icon.ico"; Comment: "{cm:ShortcutComment}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\runtime\pythonw.exe"; Parameters: "-B ""{app}\app\windows_main.py"""; WorkingDir: "{app}"; IconFilename: "{app}\app\assets\icon.ico"; Comment: "{cm:ShortcutComment}"; Tasks: desktopicon

[Run]
; Senza skipifsilent: dopo un aggiornamento silenzioso il programma riparte da solo.
Filename: "{app}\runtime\pythonw.exe"; Parameters: "-B ""{app}\app\windows_main.py"""; WorkingDir: "{app}"; Description: "{cm:LaunchAfter}"; Flags: nowait postinstall

[Code]
// Il programma usa un mutex per l'istanza unica. Durante un aggiornamento
// lanciato dal programma stesso il setup aspetta che si chiuda (fino a 30 s);
// altrimenti chiede di chiuderlo.
function WaitForApp(Silent: Boolean): Boolean;
var
  Tries: Integer;
begin
  Result := True;
  Tries := 0;
  while CheckForMutexes('{#AppMutex}') and Silent and (Tries < 60) do
  begin
    Sleep(500);
    Tries := Tries + 1;
  end;
  while CheckForMutexes('{#AppMutex}') do
  begin
    if SuppressibleMsgBox(CustomMessage('AppRunning'), mbError, MB_RETRYCANCEL, IDCANCEL) <> IDRETRY then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := WaitForApp(WizardSilent);
end;

function InitializeUninstall(): Boolean;
begin
  Result := WaitForApp(UninstallSilent);
end;
