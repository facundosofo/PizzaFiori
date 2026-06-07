@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0rename_imagenes.ps1" %*
pause
