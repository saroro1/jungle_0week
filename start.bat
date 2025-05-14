@echo off

echo 사용할 가상 환경 폴더 이름을 입력하세요 (기본값: .venv). 엔터를 누르면 기본값이 적용됩니다.
set /p USER_VENV_INPUT=

REM 입력이 비어 있는지 확인하고 VENV_DIR 설정
if "%USER_VENV_INPUT%"=="" (
    set VENV_DIR=.venv
    echo 가상 환경 폴더 이름으로 기본값 '%VENV_DIR%' 를 사용합니다.
) else (
    set VENV_DIR=%USER_VENV_INPUT%
    echo 가상 환경 폴더 이름으로 '%VENV_DIR%' 를 사용합니다.
)

echo 가상 환경 '%VENV_DIR%' 생성 중...
if %ERRORLEVEL% NEQ 0 (
    echo 오류: 가상 환경 생성에 실패했습니다. Python이 설치되어 있고 venv 모듈을 사용할 수 있는지 확인하세요.
    exit /b 1
)
echo 가상 환경 생성 완료.

echo 가상 환경 활성화 중...
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
    echo 가상 환경 활성화 완료.
) else (
    echo 오류: 가상 환경 활성화 스크립트를 찾을 수 없습니다. 가상 환경이 올바르게 생성되었는지 확인하세요.
    exit /b 1
)

REM --- 의존성 설치 ---
set APP_EXIT_STATUS=0

if exist "requirements.txt" (
  echo requirements.txt에서 의존성 설치 중...
  pip install -r requirements.txt
  if %ERRORLEVEL% NEQ 0 (
      echo 오류: 의존성 설치에 실패했습니다.
      set APP_EXIT_STATUS=1 REM 의존성 설치 실패도 에러 상태로 기록
  ) else (
      echo 의존성 설치 완료.
  )
) else (
  echo 경고: requirements.txt 파일을 찾을 수 없습니다. 의존성 설치를 건너뜁니다.
)

REM --- 애플리케이션 실행 --
if exist "app.py" (
  echo 'app.py' 실행 중...
  python app.py
  set APP_EXIT_STATUS=%ERRORLEVEL%
  echo 'app.py' 실행 완료 (종료 코드: %APP_EXIT_STATUS%).
) else (
  echo 오류: app.py 파일을 찾을 수 없습니다. 애플리케이션을 실행할 수 없습니다.
  set APP_EXIT_STATUS=1 REM app.py가 없으면 에러로 간주합니다.
)

REM --- 가상 환경 비활성화 ---
echo 가상 환경 비활성화 중...
deactivate
echo 가상 환경 비활성화 완료.

REM --- 스크립트 종료 ---   
exit /b %APP_EXIT_STATUS%