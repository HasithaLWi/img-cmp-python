@echo off
title Building PixelScan with Nuitka (C Compilation)...
echo ===================================================
echo   Building PixelScan with Nuitka (C Machine Code)
echo ===================================================

echo.
echo [1/3] Compiling with MSVC C Compiler (Please wait)...
call ".venv\Scripts\python.exe" -m nuitka ^
  --standalone ^
  --windows-console-mode=disable ^
  --enable-plugin=tk-inter ^
  --include-package-data=customtkinter ^
  --output-dir=dist\PixelScan_Nuitka ^
  --assume-yes-for-downloads ^
  src\my_app\main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Nuitka build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Copying Documentation to dist\PixelScan_Nuitka\main.dist\...
copy /Y "README.txt" "dist\PixelScan_Nuitka\main.dist\" >nul
copy /Y "HOW_TO_USE.txt" "dist\PixelScan_Nuitka\main.dist\" >nul
copy /Y "LICENSE" "dist\PixelScan_Nuitka\main.dist\" >nul

echo.
echo [3/3] Build Succeeded!
echo Output folder: dist\PixelScan_Nuitka\main.dist\
echo Executable   : dist\PixelScan_Nuitka\main.dist\main.exe
echo ===================================================
echo.
pause
