@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  if errorlevel 1 goto falha
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto falha
)
.venv\Scripts\python.exe -m scripts.configurar_env
echo Confira o .env e prepare o banco conforme o README antes do primeiro acesso.
.venv\Scripts\python.exe app.py
pause
exit /b
:falha
echo Nao foi possivel preparar o Python. Consulte o README.
pause
exit /b 1
