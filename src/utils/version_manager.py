import os
import json
import logging
from pathlib import Path

class VersionManager:
    CURRENT_VERSION = "1.1.0"  # 현재 프로그램 버전
    VERSION_FILE = "version_info.json"
    
    @staticmethod
    def get_version_file_path():
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', VersionManager.VERSION_FILE)
    
    @staticmethod
    def initialize_version_file():
        """버전 파일이 없으면 생성합니다."""
        version_file = VersionManager.get_version_file_path()
        if not os.path.exists(version_file):
            version_info = {
                "version": VersionManager.CURRENT_VERSION,
                "model_version": VersionManager.CURRENT_VERSION
            }
            VersionManager.save_version_info(version_info)
            return version_info
        return VersionManager.load_version_info()

    @staticmethod
    def load_version_info():
        """버전 정보를 로드합니다."""
        try:
            version_file = VersionManager.get_version_file_path()
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return VersionManager.initialize_version_file()
        except Exception as e:
            logging.error(f"Error loading version info: {str(e)}")
            return {"version": "0.0.0", "model_version": "0.0.0"}

    @staticmethod
    def save_version_info(version_info):
        """버전 정보를 저장합니다."""
        try:
            version_file = VersionManager.get_version_file_path()
            os.makedirs(os.path.dirname(version_file), exist_ok=True)
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving version info: {str(e)}")

    @staticmethod
    def check_version_compatibility():
        """버전 호환성을 확인하고 필요한 작업을 수행합니다."""
        version_info = VersionManager.load_version_info()
        stored_version = version_info.get("version", "0.0.0")
        
        if VersionManager.compare_versions(stored_version, VersionManager.CURRENT_VERSION) < 0:
            # 버전이 업데이트되었을 때 수행할 작업
            VersionManager.handle_version_update(stored_version)
            
            # 버전 정보 업데이트
            version_info["version"] = VersionManager.CURRENT_VERSION
            version_info["model_version"] = VersionManager.CURRENT_VERSION
            VersionManager.save_version_info(version_info)
            return True
        return False

    @staticmethod
    def compare_versions(version1, version2):
        """두 버전을 비교합니다. version1이 더 낮으면 -1, 같으면 0, 높으면 1을 반환합니다."""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        return 0

    @staticmethod
    def handle_version_update(old_version):
        """버전 업데이트 시 필요한 작업을 수행합니다."""
        try:
            # 이전 모델 파일 삭제
            model_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'inquiry_classifier.joblib')
            if os.path.exists(model_file):
                os.remove(model_file)
                logging.info(f"Removed old model file due to version update from {old_version} to {VersionManager.CURRENT_VERSION}")
        except Exception as e:
            logging.error(f"Error handling version update: {str(e)}")