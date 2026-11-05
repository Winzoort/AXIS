@echo off
title AXIS - Servidor local

cd /d "%~dp0"

set AXIS_SECRET_KEY=TU_CLAVE
set AXIS_ADMIN_USER=TU_USUARIO
set AXIS_ADMIN_PASSWORD=TU_CONTRASEÑA

py app.py

pause