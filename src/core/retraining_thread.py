# src/core/training_thread.py
import logging
import pandas as pd
import time
from PyQt6.QtCore import QThread, pyqtSignal
from utils.text_extension import TextExtension

class RetrainingThread(QThread):
    """재학습을 위한 스레드"""
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, classifier, training_data, content_column, category_column):
        super().__init__()
        self.classifier = classifier
        self.training_data = training_data
        self.content_column = content_column
        self.category_column = category_column
        self.start_time = None
        self.is_processing_done = False
        
    def update_progress(self):
        """진행률을 업데이트합니다."""
        MAX_TIME = 97  # 1분 37초
        FINAL_PROGRESS_TIME = 3  # 3초
        
        while not self.is_processing_done:
            elapsed_time = time.time() - self.start_time
            if elapsed_time < MAX_TIME:
                progress = min(97, int((elapsed_time / MAX_TIME) * 100))
                self.progress_updated.emit(progress)
            time.sleep(1)
            
        # 처리가 완료되면 3초에 걸쳐 100%까지 증가
        current_progress = min(97, int((time.time() - self.start_time) / MAX_TIME * 100))
        steps_remaining = 100 - current_progress
        sleep_time = FINAL_PROGRESS_TIME / steps_remaining
        
        for progress in range(current_progress + 1, 101):
            self.progress_updated.emit(progress)
            time.sleep(sleep_time)

    def run(self):
        try:
            self.start_time = time.time()
            self.is_processing_done = False
            
            # 진행률 업데이트를 위한 새 스레드 시작
            progress_thread = QThread()
            progress_thread.run = self.update_progress
            progress_thread.start()
            
            logging.info("Starting retraining process")
            
            # 텍스트 전처리
            preprocessed_data = self.training_data.copy()
            preprocessed_data[self.content_column] = preprocessed_data[self.content_column].apply(TextExtension.clean_text)
            
            # 재학습 수행
            self.classifier.train(
                preprocessed_data[self.content_column].fillna(''),
                preprocessed_data[self.category_column]
            )
            self.classifier.save_model()
            logging.info("Model retrained and saved")
            
            # 처리 완료 표시
            self.is_processing_done = True
            progress_thread.wait()

            self.finished.emit()
            
        except Exception as e:
            logging.error(f"Error during retraining: {str(e)}", exc_info=True)
            self.error.emit(str(e))
            self.is_processing_done = True