@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set PY=py -3.13
where py >nul 2>nul
if errorlevel 1 (
  echo py.exe not found on PATH. Install Python 3.14 or 3.13 first.
  exit /b 1
)

echo ==========================================
echo Storage Cleaner - building...
echo ==========================================
echo.

echo [1/3] Building onedir (dist\Storage Cleaner\)...
%PY% -m PyInstaller --noconfirm --clean --windowed --onedir ^
  --name "Storage Cleaner" ^
  --icon "icon.ico" ^
  --version-file "build\version_info.txt" ^
  --add-data "src\ui;ui" ^
  --collect-all webview ^
  --paths "src" ^
  "src\app.py"
if errorlevel 1 (
  echo.
  echo Onedir build failed. Retrying without icon/version_info...
  %PY% -m PyInstaller --noconfirm --clean --windowed --onedir ^
    --name "Storage Cleaner" ^
    --add-data "src\ui;ui" ^
    --collect-all webview ^
    --paths "src" ^
    "src\app.py"
  if errorlevel 1 exit /b 1
)

echo.
echo [2/3] Building onefile (dist\Storage Cleaner Portable.exe)...
%PY% -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name "Storage Cleaner Portable" ^
  --icon "icon.ico" ^
  --version-file "build\version_info.txt" ^
  --add-data "src\ui;ui" ^
  --collect-all webview ^
  --paths "src" ^
  "src\app.py"
if errorlevel 1 (
  echo Onefile build failed. Retrying without icon/version_info...
  %PY% -m PyInstaller --noconfirm --clean --windowed --onefile ^
    --name "Storage Cleaner Portable" ^
    --add-data "src\ui;ui" ^
    --collect-all webview ^
    --paths "src" ^
    "src\app.py"
  if errorlevel 1 exit /b 1
)

echo.
echo [3/3] Zipping onedir for distribution...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\Storage Cleaner\*' -DestinationPath 'dist\Storage-Cleaner-v1.0.zip' -Force"

echo.
echo ==========================================
echo Build complete.
echo.
echo   Folder:     dist\Storage Cleaner\Storage Cleaner.exe
echo   Portable:   dist\Storage Cleaner Portable.exe
echo   Zip:        dist\Storage-Cleaner-v1.0.zip
echo.
echo Share the Portable .exe with friends - they just double-click it.
echo ==========================================
endlocal
