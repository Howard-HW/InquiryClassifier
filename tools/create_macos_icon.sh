#!/bin/bash

# create_macos_icon.sh

# 입력 파일 확인
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 input_image.png"
    echo "Please provide a 1024x1024 PNG image file"
    exit 1
fi

INPUT_FILE="$1"

# 입력 파일 존재 확인
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

# 둥근 모서리 이미지 생성
# ROUNDED_FILE="rounded_$INPUT_FILE"
# convert "$INPUT_FILE" -alpha set -background none -gravity center -extent 1024x1024 "$ROUNDED_FILE"

# 임시 작업 디렉토리 생성
ICONSET_NAME="app.iconset"
rm -rf $ICONSET_NAME
mkdir $ICONSET_NAME

# 다양한 크기의 아이콘 생성
ICON_SIZES=("16" "32" "128" "256" "512")

for size in "${ICON_SIZES[@]}"; do
    # 기본 크기
    sips -z $size $size "$INPUT_FILE" --out "$ICONSET_NAME/icon_${size}x${size}.png"
    
    # @2x 크기
    let "double_size = $size * 2"
    sips -z $double_size $double_size "$INPUT_FILE" --out "$ICONSET_NAME/icon_${size}x${size}@2x.png"
done

# .icns 파일 생성
mkdir -p src/resources/system
iconutil -c icns $ICONSET_NAME -o ./src/resources/system/app_icon.icns

# 임시 파일 정리
rm -rf $ICONSET_NAME

echo "App icon created successfully at ./src/resources/system/app_icon.icns"