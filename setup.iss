[Setup]
; =====================================================================
; TEM Segmenter - Inno Setup Script
; =====================================================================
AppName=TEM Segmenter
AppVersion=1.0
AppPublisher=TEM Lab
DefaultDirName={localappdata}\TEM_Segmenter
DefaultGroupName=TEM Segmenter
OutputDir=.\Instalador
OutputBaseFilename=Instalar_TEM_Segmenter
Compression=lzma2/ultra
SolidCompression=yes
PrivilegesRequired=lowest
; Descomenta si agregas un icono:
; SetupIconFile=assets\icon.ico
; UninstallDisplayIcon={app}\assets\icon.ico

[Files]
; Copia todo el proyecto al destino, excluyendo entornos virtuales,
; cache de Python, el propio instalador y la carpeta de salida.
Source: "*"; DestDir: "{app}"; Excludes: "venv\*;Instalador\*;.git\*;.venv\*;__pycache__\*;*.iss"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TEM Segmenter"; Filename: "{app}\launcher.bat"
Name: "{userdesktop}\TEM Segmenter"; Filename: "{app}\launcher.bat"
; Si agregas icono:
; Name: "{group}\TEM Segmenter"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\assets\icon.ico"
; Name: "{userdesktop}\TEM Segmenter"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\assets\icon.ico"

[Run]
Filename: "{app}\launcher.bat"; Description: "Ejecutar TEM Segmenter ahora"; Flags: postinstall nowait
