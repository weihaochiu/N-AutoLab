@echo off
setlocal
title N-AutoLab Phase 1 - SIMULATION
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Run setup_windows.bat first.
  exit /b 1
)
set QT_API=pyside6
".venv\Scripts\python.exe" -m nautolab.gui
