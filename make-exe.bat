@echo off

setlocal EnableDelayedExpansion

::: Build and Sign the exe
python build.py

signtool sign /a /s MY /n "NGN Management Inc."  /tr http://timestamp.sectigo.com /fd SHA256 /td SHA256 /v dist\SDIF-Merge\SDIF-Merge.exe

::: Build the installer

makensis sdif_merge.nsi

::: Clean up build artifacts
rmdir /q/s build
