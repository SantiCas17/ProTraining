@echo off
title ProTraining - Servidor Local
echo ==============================================
echo      Iniciando el Motor de ProTraining...
echo ==============================================

:: Nos movemos a la carpeta donde está este archivo
cd /d "%~dp0"

:: Activamos el entorno virtual
call venv\Scripts\activate.bat

:: Abrimos el navegador predeterminado en la ruta del dashboard
start http://127.0.0.1:8000/

:: Levantamos el servidor de Django
python manage.py runserver

pause