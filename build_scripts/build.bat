@echo off

echo Checking Python version...
python --version > temp.txt
set /p PYTHON_VERSION=<temp.txt
del temp.txt

echo Current Python version: %PYTHON_VERSION%

REM Python 3.12인 경우 경고
echo %PYTHON_VERSION% | findstr "3.12" > nul
if %errorlevel% equ 0 (
    echo Warning: Python 3.12 may cause compatibility issues.
    echo Please install Python 3.11 from https://www.python.org/downloads/release/python-3115/
    echo After installation, make sure Python 3.11 is set as your default Python version.
    exit /b 1
)

echo Creating build directory...
if not exist build mkdir build
cd build

echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt
pip install pyinstaller

echo Building executable...
pyinstaller --name="InquiryClassifier" ^
            --onefile ^
            --windowed ^
            --add-data="src/resources;resources" ^
            --hidden-import=sklearn ^
            --hidden-import=pandas ^
            --hidden-import=numpy ^
            --hidden-import=joblib ^
            --hidden-import=openpyxl ^
            --paths="src" ^
            src/main.py