@echo off
REM KSTAR MCP PoC v2 - Windows 자동 설치 스크립트

echo 🚀 KSTAR MCP PoC v2 설치를 시작합니다...
echo ================================================

REM 현재 디렉토리로 이동
cd /d "%~dp0"

echo 📁 작업 디렉토리: %CD%

REM Python 확인
echo 🐍 Python 버전 확인...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo    Python 3.8 이상을 설치해주세요.
    echo    https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python 발견

REM 가상환경 생성
echo 🔧 가상환경 생성...
if not exist "venv" (
    python -m venv venv
    echo ✅ 가상환경 생성 완료
) else (
    echo ⚠️  가상환경이 이미 존재합니다.
)

REM 가상환경 활성화
echo 🔌 가상환경 활성화...
call venv\Scripts\activate.bat

REM pip 업그레이드
echo 📦 pip 업그레이드...
python -m pip install --upgrade pip

REM 의존성 설치
echo 📚 Python 패키지 설치...
pip install -r requirements.txt

REM 환경 설정 파일 생성
echo ⚙️  환경 설정 파일 생성...
if not exist ".env" (
    copy config.env.example .env
    echo ✅ .env 파일 생성 완료
    echo ⚠️  .env 파일에 OpenAI API 키를 추가해주세요!
) else (
    echo ⚠️  .env 파일이 이미 존재합니다.
)

echo.
echo ================================================
echo 🎉 설치가 완료되었습니다!
echo.
echo 📋 다음 단계:
echo 1. OpenAI API 키 설정 (선택사항):
echo    notepad .env
echo    # OPENAI_API_KEY=your_api_key_here
echo.
echo 2. 애플리케이션 실행:
echo    venv\Scripts\activate.bat
echo    python main.py
echo.
echo 3. 웹 브라우저에서 접속:
echo    http://localhost:8000
echo.
echo 💡 팁: API 키 없이도 데모 모드로 실행됩니다!
echo ================================================
pause
