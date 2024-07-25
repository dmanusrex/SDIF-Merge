; NSIS Installer for SDIF Merge
; The name of the installer
Name "Swimming Canada - SDIF Merge"

OutFile "SDIF-Merge.exe"

; Build Unicode installer
Unicode True

!define MUI_ICON media\sdifmerge.ico
!define MUI_UNICON media\sdifmerge.ico


!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY "${UNINSTKEY}"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME "CurrentUser"
!define MULTIUSER_INSTALLMODE_INSTDIR "$(^Name)"
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI

!include "LogicLib.nsh"
!include "MultiUser.nsh"
!include "MUI2.nsh"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  !insertmacro MULTIUSER_INIT
FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
FunctionEnd

!finalize 'signtool sign /a /s MY /n "NGN Management Inc." /fd SHA256 /td SHA256 /tr http://timestamp.sectigo.com /v "%1"' = 0 ; %1 is replaced by the install exe to be signed.
!uninstfinalize 'signtool sign /a /s MY /n "NGN Management Inc." /fd SHA256 /td SHA256 /tr http://timestamp.sectigo.com /v "%1"' = 0 ; %1 is replaced by the uninstaller exe to be signed

;--------------------------------

; The stuff to install
Section "SDIF Merge (required)"

  SectionIn RO

  ; Set output path to the installation directory.
  SetOutPath $InstDir

  WriteUninstaller "$InstDir\Uninstall.exe"
  WriteRegStr ShCtx "${UNINSTKEY}" DisplayName "$(^Name)"
  WriteRegStr ShCtx "${UNINSTKEY}" UninstallString '"$InstDir\Uninstall.exe"'
  WriteRegStr ShCtx "${UNINSTKEY}" $MultiUser.InstallMode 1 ; Write MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME so the correct context can be detected in the uninstaller.

  ; Put file there
  File /r "dist\SDIF-Merge\*.*"

SectionEnd

; Optional section (can be disabled by the user)

Section "Start Menu shortcut"
  CreateShortcut /NoWorkingDir "$SMPrograms\$(^Name).lnk" "$InstDir\SDIF-Merge.exe"
SectionEnd

Section "Desktop Shortcut"

  CreateShortcut "$DESKTOP\SDIF Merge.lnk" "$INSTDIR\SDIF-Merge.exe"

SectionEnd
;--------------------------------

; Uninstaller

Section "Uninstall"


  ; Remove files and uninstaller

  RMdir /r "$INSTDIR\"

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\$(^Name).lnk"
  Delete "$DESKTOP\SDIF Merge.lnk"

  ; Remove registry keys
  DeleteRegKey ShCtx "${UNINSTKEY}"
  RMDir "$INSTDIR"

SectionEnd
