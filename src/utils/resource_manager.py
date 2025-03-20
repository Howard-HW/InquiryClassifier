import os
import sys
import logging
from pathlib import Path

class ResourceManager:
    RESOURCE_DIR = 'resources'
    
    @staticmethod
    def get_resource_path(relative_path, is_system_resource=True):
        """리소스 파일의 절대 경로를 반환합니다."""
        try:
            if is_system_resource:
                # 시스템 리소스는 실행 파일 내부에서 찾음
                if hasattr(sys, '_MEIPASS'):
                    base_path = sys._MEIPASS
                else:
                    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                if relative_path.startswith('resources/'):
                    full_path = os.path.join(base_path, relative_path)
                else:
                    full_path = os.path.join(base_path, 'resources/system', relative_path)
            else:
                # 사용자 리소스는 실행 파일과 같은 디렉토리에서 찾음
                if hasattr(sys, '_MEIPASS'):
                    base_path = os.path.dirname(sys.executable)
                else:
                    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                full_path = os.path.join(base_path, relative_path)
            
            if not os.path.exists(full_path):
                logging.warning(f"Resource not found: {full_path}")
                return None
                
            logging.debug(f"Resource path resolved: {full_path}")
            return full_path
            
        except Exception as e:
            logging.error(f"Error resolving resource path: {str(e)}")
            return None

    @staticmethod
    def save_user_resource(filename, content):
        """사용자 리소스 파일을 저장합니다."""
        try:
            if hasattr(sys, '_MEIPASS'):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            full_path = os.path.join(base_path, filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"User resource saved: {full_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving user resource: {str(e)}")
            return False
