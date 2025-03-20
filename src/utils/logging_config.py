import logging
import os
import json
from datetime import datetime
from .resource_manager import ResourceManager

def setup_logging():
    """로깅 설정을 초기화하는 함수"""
    try:
        # macOS의 적절한 로그 디렉토리 설정
        home = os.path.expanduser("~")
        log_dir = os.path.join(
            home,
            "Library",
            "Logs",
            "InquiryClassifier"
        )
        
        # 로그 디렉토리 생성
        os.makedirs(log_dir, exist_ok=True)
        
        # 로그 파일명 설정
        log_file = os.path.join(
            log_dir, 
            f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        # 로깅 기본 설정
        logging.basicConfig(
            level=logging.ERROR,  # 기본 레벨을 ERROR로 설정
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(
                    filename=log_file,
                    encoding='utf-8',
                    mode='a'
                ),
                logging.StreamHandler()
            ]
        )

    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        # 로깅 설정에 실패하더라도 프로그램은 계속 실행되도록 함
        logging.basicConfig(level=logging.ERROR)

def get_logger(name):
    """특정 모듈용 로거를 반환하는 함수"""
    return logging.getLogger(name)