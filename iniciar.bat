@echo off
title Cartorio 6BPM - Sistema
color 0A

echo ========================================
echo   Cartorio 6BPM - Inicializando
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Iniciando Backend (Django)...
start "Backend" cmd /k "python manage.py runserver 8000"

timeout /t 3 /nobreak > nul

echo [2/2] Iniciando Frontend (React)...
cd frontend
start "Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   Sistema Iniciado!
echo ========================================
echo.
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:5173
echo.
echo   Pressione qualquer tecla para sair...
pause > nul
