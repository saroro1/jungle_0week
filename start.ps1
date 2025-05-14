# 스크립트 시작 시 출력 인코딩을 UTF-8로 설정 (필요에 따라)
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "사용할 가상 환경 폴더 이름을 입력하세요 (기본값: .venv). 엔터를 누르면 기본값이 적용됩니다."
$UserVenvInput = Read-Host
$VenvDir = if ([string]::IsNullOrEmpty($UserVenvInput)) { ".venv" } else { $UserVenvInput }

if ($VenvDir -eq ".venv") {
    Write-Host "가상 환경 폴더 이름으로 기본값 '$VenvDir' 를 사용합니다."
} else {
    Write-Host "가상 환경 폴더 이름으로 '$VenvDir' 를 사용합니다."
}

Write-Host "가상 환경 '$VenvDir' 생성 중..."
python -m venv "$VenvDir"
if ($LASTEXITCODE -ne 0) {
    Write-Error "오류: 가상 환경 생성에 실패했습니다. Python이 설치되어 있고 venv 모듈을 사용할 수 있는지 확인하세요."
    exit 1
}
Write-Host "가상 환경 생성 완료."

Write-Host "가상 환경 활성화 중..."
$ActivateScriptPath = Join-Path -Path $VenvDir -ChildPath "Scripts\Activate.ps1"

if (Test-Path $ActivateScriptPath) {
    . $ActivateScriptPath  # 점(.) 소싱으로 스크립트를 현재 세션에서 실행
    Write-Host "가상 환경 활성화 완료."
} else {
    Write-Error "오류: 가상 환경 활성화 스크립트($ActivateScriptPath)를 찾을 수 없습니다. 가상 환경이 올바르게 생성되었는지 확인하세요."
    exit 1
}

$AppExitStatus = 0

if (Test-Path "requirements.txt") {
  Write-Host "requirements.txt에서 의존성 설치 중..."
  pip install -r requirements.txt
  if ($LASTEXITCODE -ne 0) {
      Write-Error "오류: 의존성 설치에 실패했습니다."
      $AppExitStatus = 1
  } else {
      Write-Host "의존성 설치 완료."
  }
} else {
  Write-Warning "경고: requirements.txt 파일을 찾을 수 없습니다. 의존성 설치를 건너뜁니다."
}

if (Test-Path "app.py") {
  Write-Host "'app.py' 실행 중..."
  python app.py
  $AppExitStatus = $LASTEXITCODE # app.py의 종료 코드를 반영
  Write-Host "'app.py' 실행 완료 (종료 코드: $AppExitStatus)."
} else {
  Write-Error "오류: app.py 파일을 찾을 수 없습니다. 애플리케이션을 실행할 수 없습니다."
  $AppExitStatus = 1
}

# deactivate 명령어는 activate.ps1에 의해 정의된 함수이므로 바로 호출 가능
Write-Host "가상 환경 비활성화 중..."
deactivate
Write-Host "가상 환경 비활성화 완료."

exit $AppExitStatus