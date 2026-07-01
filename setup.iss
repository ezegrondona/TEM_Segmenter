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
; Descomenta y cambia las siguientes lineas si agregas un icono
; SetupIconFile=assets\icon.ico
; UninstallDisplayIcon={app}\assets\icon.ico

[Files]
; Copiamos todo el contenido de la carpeta actual al destino
; Ignoramos el entorno virtual (venv), la carpeta git, la cache de python y el script de inno setup
Source: "*"; DestDir: "{app}"; Excludes: "venv, Instalador, .git, .venv, __pycache__, *.iss"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Crea los accesos directos en el Menu Inicio y en el Escritorio apuntando al launcher.bat
Name: "{group}\TEM Segmenter"; Filename: "{app}\launcher.bat"
Name: "{userdesktop}\TEM Segmenter"; Filename: "{app}\launcher.bat"
; Si usas icono, agregalo asi:
; Name: "{group}\TEM Segmenter"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\assets\icon.ico"
; Name: "{userdesktop}\TEM Segmenter"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\assets\icon.ico"

[Run]
; Opcion al finalizar para ejecutar el programa inmediatamente
Filename: "{app}\launcher.bat"; Description: "Ejecutar TEM Segmenter ahora"; Flags: postinstall nowait
