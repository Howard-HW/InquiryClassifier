#!/usr/bin/env python3
import sys
from PIL import Image
import argparse

def create_ico(input_file, output_file, sizes=None):
    """PNG 파일을 ICO 파일로 변환

    Args:
        input_file (str): 입력 PNG 파일 경로
        output_file (str): 출력 ICO 파일 경로
        sizes (list, optional): 아이콘 크기 리스트. 기본값은 표준 크기들.
    """
    if sizes is None:
        sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    
    try:
        img = Image.open(input_file)
        img.save(output_file, format='ICO', sizes=sizes)
        print(f"Successfully created {output_file}")
    except Exception as e:
        print(f"Error creating ICO file: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert PNG to ICO')
    parser.add_argument('input', help='Input PNG file')
    parser.add_argument('output', help='Output ICO file')
    args = parser.parse_args()

    create_ico(args.input, args.output)

if __name__ == "__main__":
    main()