@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or newer from https://www.python.org/downloads/
  pause
  exit /b 1
)

python --version >nul 2>nul
if errorlevel 1 (
  echo Python is pointing to the Windows Store alias instead of a real Python install.
  echo Install Python from https://www.python.org/downloads/ and enable Add python.exe to PATH.
  echo Then turn off Windows App execution aliases for python.exe and python3.exe.
  pause
  exit /b 1
)

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python --version >nul 2>nul
if errorlevel 1 (
  echo The existing .venv was created with a broken Python path.
  echo Delete the .venv folder after installing Python from python.org, then run this file again.
  pause
  exit /b 1
)

python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
