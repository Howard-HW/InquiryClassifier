class TextExtension:
    @staticmethod
    def clean_text(text):
        """텍스트에서 특정 문자열 이후의 내용을 제거합니다."""
        if not isinstance(text, str):
            return str(text)
            
        # "os:" 이후 텍스트 제거
        if "os:" in text.lower():
            text = text.split("os:", 1)[0]
            
        # "문의경로:" 이후 텍스트 제거
        if "문의경로:" in text:
            text = text.split("문의경로:", 1)[0]
            
        # 결과 텍스트 정리
        return text.strip()