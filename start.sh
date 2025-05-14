#!/bin/bash

echo "사용할 가상 환경 폴더 이름을 입력하세요 (기본값: .venv). 엔터를 누르면 기본값이 적용됩니"
read USER_VENV_INPUT

if [ -z "$USER_VENV_INPUT" ]; then
    VENV_DIR=".venv"
    echo "가상 환경 폴더 이름으로 기본값 '$VENV_DIR' 를 사용합니다."
else
    VENV_DIR="$USER_VENV_INPUT"
    echo "가상 환경 폴더 이름으로 '$VENV_DIR' 를 사용합니다."
fi

echo "가상 환경 '$VENV_DIR' 생성 중..."
if ! python3 -m venv "$VENV_DIR"; then
    echo "오류: 가상 환경 생성에 실패했습니다. python3가 설치되어 있고 venv 모듈을 사용할 수 있는지 확인하세요."
    exit 1
fi
echo "가상 환경 생성 완료."

echo "가상 환경 활성화 중..."
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "가상 환경 활성화 완료."
else
    echo "오류: 가상 환경 활성화 스크립트를 찾을 수 없습니다. 가상 환경이 올바르게 생성되었는지 확인하세요."
    exit 1
fi

APP_EXIT_STATUS=0

if [ -f "requirements.txt" ]; then
  echo "requirements.txt에서 의존성 설치 중..."
  if ! pip install -r requirements.txt; then
      echo "오류: 의존성 설치에 실패했습니다."
      APP_EXIT_STATUS=1
  else
      echo "의존성 설치 완료."
  fi
else
  echo "경고: requirements.txt 파일을 찾을 수 없습니다. 의존성 설치를 건너뜁니다."
fi

if [ -f "app.py" ]; then
  echo "'app.py' 실행 중..."
  python app.py
  APP_EXIT_STATUS=$?
  echo "'app.py' 실행 완료 (종료 코드: $APP_EXIT_STATUS)."
else
  echo "오류: app.py 파일을 찾을 수 없습니다. 애플리케이션을 실행할 수 없습니다."
  APP_EXIT_STATUS=1
fi

echo "가상 환경 비활성화 중..."
deactivate
echo "가상 환경 비활성화 완료."

exit $APP_EXIT_STATUS