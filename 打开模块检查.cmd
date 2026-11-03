@echo off
set "CAD_EXE=%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecad.exe"
if not exist "%CAD_EXE%" (
  echo Open CAD_v2/scripts/inspect_modules.FCMacro from the FreeCAD Macro menu.
  pause
  exit /b 1
)
start "" "%CAD_EXE%" "%~dp0CAD_v2\scripts\inspect_modules.FCMacro"
