@echo off
title Building PixelScan with PyInstaller...
echo ===================================================
echo   Building PixelScan (PyInstaller Standalone)
echo ===================================================

echo.
echo [1/3] Running PyInstaller...
call ".venv\Scripts\pyinstaller.exe" ^
  --name "PixelScan" ^
  --windowed ^
  --onedir ^
  --noconfirm ^
  --clean ^
  --add-data ".venv\Lib\site-packages\customtkinter;customtkinter\" ^
  --paths "." ^
  src\my_app\main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Check the output above.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Copying Documentation to dist\PixelScan\...
copy /Y "README.txt" "dist\PixelScan\" >nul
copy /Y "HOW_TO_USE.txt" "dist\PixelScan\" >nul
copy /Y "LICENSE" "dist\PixelScan\" >nul

echo.
echo [3/3] Build Succeeded!
echo Output folder: dist\PixelScan\
echo Executable   : dist\PixelScan\PixelScan.exe
echo ===================================================
echo.
pause
