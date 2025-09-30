#!/bin/bash

# KSTAR MCP PoC v2 - 자동 설치 스크립트
# 이 스크립트는 프로젝트를 처음 사용하는 사용자를 위한 것입니다.

set -e  # 오류 발생시 스크립트 중단

echo "🚀 KSTAR MCP PoC v2 설치를 시작합니다..."
echo "================================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📁 작업 디렉토리: $SCRIPT_DIR${NC}"

# Python 버전 확인
echo -e "${BLUE}🐍 Python 버전 확인...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3가 설치되지 않았습니다.${NC}"
    echo "   Python 3.8 이상을 설치해주세요."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION 발견${NC}"

# 가상환경 생성
echo -e "${BLUE}🔧 가상환경 생성...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ 가상환경 생성 완료${NC}"
else
    echo -e "${YELLOW}⚠️  가상환경이 이미 존재합니다.${NC}"
fi

# 가상환경 활성화
echo -e "${BLUE}🔌 가상환경 활성화...${NC}"
source venv/bin/activate

# pip 업그레이드
echo -e "${BLUE}📦 pip 업그레이드...${NC}"
pip install --upgrade pip

# 의존성 설치
echo -e "${BLUE}📚 Python 패키지 설치...${NC}"
pip install -r requirements.txt

# 환경 설정 파일 생성
echo -e "${BLUE}⚙️  환경 설정 파일 생성...${NC}"
if [ ! -f ".env" ]; then
    cp config.env.example .env
    echo -e "${GREEN}✅ .env 파일 생성 완료${NC}"
    echo -e "${YELLOW}⚠️  .env 파일에 OpenAI API 키를 추가해주세요!${NC}"
else
    echo -e "${YELLOW}⚠️  .env 파일이 이미 존재합니다.${NC}"
fi

# 실행 권한 부여
chmod +x main.py

echo ""
echo "================================================"
echo -e "${GREEN}🎉 설치가 완료되었습니다!${NC}"
echo ""
echo -e "${BLUE}📋 다음 단계:${NC}"
echo "1. OpenAI API 키 설정 (선택사항):"
echo "   nano .env"
echo "   # OPENAI_API_KEY=your_api_key_here"
echo ""
echo "2. 애플리케이션 실행:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. 웹 브라우저에서 접속:"
echo "   http://localhost:8000"
echo ""
echo -e "${YELLOW}💡 팁: API 키 없이도 데모 모드로 실행됩니다!${NC}"
echo "================================================"
