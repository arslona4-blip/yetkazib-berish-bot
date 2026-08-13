@echo off
cd /d "%~dp0"
if not exist node_modules (
  echo Paketlar o'rnatilmoqda...
  call npm install
)
echo Ofis nazorat ochilmoqda...
call npm run desktop
pause
