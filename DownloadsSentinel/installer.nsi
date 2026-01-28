; NSIS Installer Script for Windows Downloads Sentinel
; Requires NSIS 3.0+

!include "MUI2.nsh"

; General Settings
Name "Windows Downloads Sentinel"
OutFile "DownloadsSentinel_Setup.exe"
InstallDir "$PROGRAMFILES\Downloads Sentinel"
InstallDirRegKey HKCU "Software\Downloads Sentinel" ""
RequestExecutionLevel admin

; Interface Settings
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\DownloadsSentinel.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Downloads Sentinel"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; Installer Section
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy main executable
    File "dist\DownloadsSentinel.exe"
    
    ; Copy assets
    SetOutPath "$INSTDIR\assets"
    File /r "assets\*.*"
    
    ; Copy config folder
    SetOutPath "$INSTDIR\config"
    File /r "config\*.*"
    
    ; Create logs directory
    CreateDirectory "$INSTDIR\logs"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\Downloads Sentinel"
    CreateShortCut "$SMPROGRAMS\Downloads Sentinel\Downloads Sentinel.lnk" "$INSTDIR\DownloadsSentinel.exe"
    CreateShortCut "$SMPROGRAMS\Downloads Sentinel\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Create Desktop shortcut
    CreateShortCut "$DESKTOP\Downloads Sentinel.lnk" "$INSTDIR\DownloadsSentinel.exe"
    
    ; Write registry keys for uninstaller
    WriteRegStr HKCU "Software\Downloads Sentinel" "" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloads Sentinel" "DisplayName" "Downloads Sentinel"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloads Sentinel" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloads Sentinel" "DisplayIcon" "$INSTDIR\assets\icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloads Sentinel" "Publisher" "Downloads Sentinel"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloads Sentinel" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloads Sentinel" "NoRepair" 1
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove from startup registry
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "WindowsDownloadsSentinel"
    
    ; Remove files
    Delete "$INSTDIR\DownloadsSentinel.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\assets"
    RMDir /r "$INSTDIR\config"
    RMDir /r "$INSTDIR\logs"
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\Downloads Sentinel\Downloads Sentinel.lnk"
    Delete "$SMPROGRAMS\Downloads Sentinel\Uninstall.lnk"
    RMDir "$SMPROGRAMS\Downloads Sentinel"
    Delete "$DESKTOP\Downloads Sentinel.lnk"
    
    ; Remove registry keys
    DeleteRegKey HKCU "Software\Downloads Sentinel"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloads Sentinel"
SectionEnd
