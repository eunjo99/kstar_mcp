@echo off
REM KSTAR MCP PoC v2 - Windows Automated Installation Script

echo 🚀 Starting KSTAR MCP PoC v2 installation...
echo ================================================

REM Change to script directory
cd /d "%~dp0"

echo 📁 Working directory: %CD%

REM Check Python
echo 🐍 Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed.
    echo    Please install Python 3.8 or higher.
    echo    https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo 🔧 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ⚠️  Virtual environment already exists.
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📚 Installing Python packages...
pip install -r requirements.txt

REM Create environment configuration file
echo ⚙️  Creating environment configuration file...
if not exist ".env" (
    copy config.env.example .env
    echo ✅ .env file created
    echo ⚠️  Please add your OpenAI API key to .env file!
) else (
    echo ⚠️  .env file already exists.
)

echo.
echo ================================================
echo 🎉 Installation completed!
echo.
echo 📋 Next steps:
echo 1. Set up OpenAI API key (optional):
echo    notepad .env
echo    # OPENAI_API_KEY=your_api_key_here
echo.
echo 2. Run the application:
echo    venv\Scripts\activate.bat
echo    python main.py
echo.
echo 3. Open web browser:
echo    http://localhost:8000
echo.
echo 💡 Tip: Demo mode works without API key!
echo ================================================
pause


