#!/bin/bash

# 빌드 모드 설정
BUILD_MODE="release"  # or "debug"

# 디렉토리 설정
BUILD_DIR="build"
DIST_DIR="dist"
SYSTEM_RESOURCE_DIR="src/resources/system"

# 필요한 디렉토리 생성
mkdir -p $BUILD_DIR
mkdir -p $DIST_DIR

# PyInstaller 옵션 설정
PYINSTALLER_OPTS="--clean --noconfirm"

if [ "$BUILD_MODE" = "release" ]; then
    PYINSTALLER_OPTS="$PYINSTALLER_OPTS --windowed"
    PYINSTALLER_OPTS="$PYINSTALLER_OPTS --optimize=2"
    # release 모드에서는 ERROR 레벨 이상만 기록
    LOG_LEVEL="ERROR"
else
    PYINSTALLER_OPTS="$PYINSTALLER_OPTS --debug all"
    # debug 모드에서는 모든 로그 기록
    LOG_LEVEL="DEBUG"
fi

# 환경 설정
echo "Setting up virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# 필요한 패키지 설치
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# OS 확인
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS specific options
    PLATFORM_OPTS="--windowed \
        --osx-bundle-identifier=com.inquiryclassifier.app \
        --icon=src/resources/system/app_icon.icns \
        --codesign-identity=-"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Ubuntu/Linux specific options
    PLATFORM_OPTS="--windowed"
else
    echo "Unsupported operating system"
    exit 1
fi

# 공통 옵션
COMMON_OPTS="--name=InquiryClassifier \
    --collect-all sklearn \
    --add-data=src/resources/system:resources/system \
    --hidden-import=pandas \
    --hidden-import=numpy \
    --hidden-import=joblib \
    --hidden-import=openpyxl \
    --optimize=2 \
    --log-level=$LOG_LEVEL \
    --clean"

# 빌드 실행
echo "Building application in $BUILD_MODE mode..."
# 기존 빌드 파일 정리
rm -rf build dist *.spec

# PyInstaller 실행
pyinstaller $PYINSTALLER_OPTS \
    $COMMON_OPTS \
    $PLATFORM_OPTS \
    src/main.py

# macOS의 경우 추가 처리
if [[ "$OSTYPE" == "darwin"* ]]; then
    # 1. Info.plist 복사 및 권한 설정 (유지)
    cp src/resources/Info.plist ./dist/InquiryClassifier.app/Contents/
    cp src/resources/system/app_icon.icns ./dist/InquiryClassifier.app/Contents/Resources/
    chmod +x ./dist/InquiryClassifier.app/Contents/MacOS/InquiryClassifier

    # 2. 기존 코드 서명 제거 (확장)
    echo "Removing existing signatures..."
    codesign --remove-signature "./dist/InquiryClassifier.app"
    find ./dist/InquiryClassifier.app -name "*.so" -o -name "*.dylib" -o -name "Python" | while read FILE; do
        codesign --remove-signature "$FILE" || true
    done
    
    # 3. 새로운 ad-hoc 서명 추가 (확장)
    echo "Applying new signatures..."
    codesign --force --deep --sign - ./dist/InquiryClassifier.app
    
    # 서명 확인 추가
    echo "Verifying signature..."
    codesign --verify --verbose "./dist/InquiryClassifier.app"
    
    # 4. quarantine 속성 제거 (유지)
    xattr -cr ./dist/InquiryClassifier.app

    echo "macOS app bundle preparation completed"
fi
# 빌드 완료 확인
if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
    # 버전 정보 생성
    VERSION=$(date +"%Y.%m.%d")
    # 로그 레벨도 버전 정보에 포함
    echo "{\"version\": \"$VERSION\", \"build_mode\": \"$BUILD_MODE\", \"log_level\": \"$LOG_LEVEL\"}" > "$DIST_DIR/version.json"
else
    echo "Build failed!"
    exit 1
fi

# 가상환경 정리
deactivate
rm -rf venv

# 불필요한 파일 정리
rm -rf $BUILD_DIR
rm -rf __pycache__
rm -f *.spec

echo "Build process completed."