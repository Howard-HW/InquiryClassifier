# src/core/training_thread.py
import logging
import pandas as pd
import time
from PyQt6.QtCore import QThread, pyqtSignal
from .excel_handler import ExcelHandler
from utils.text_extension import TextExtension

class TrainingThread(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, classifier, input_file, output_file, should_train, selected_sheet, 
                content_column, category_column, categories):
        super().__init__()
        self.classifier = classifier
        self.input_file = input_file
        self.output_file = output_file
        self.should_train = should_train
        self.selected_sheet = selected_sheet
        self.content_column = content_column
        self.category_column = category_column
        self.categories = categories
        self.start_time = None
        self.is_processing_done = False
        
    def update_progress(self):
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
            
            logging.info(f"Processing started - Input: {self.input_file}, Sheet: {self.selected_sheet}")
            df = pd.read_excel(self.input_file, sheet_name=self.selected_sheet)
            train_df = df.copy()
            
            # 텍스트 전처리
            logging.info("Cleaning text data")
            train_df[self.content_column] = train_df[self.content_column].apply(TextExtension.clean_text)
            
            if self.should_train:
                train_data = train_df[train_df[self.category_column].notna()]
                self.classifier.train(
                    train_data[self.content_column], 
                    train_data[self.category_column]
                )
                self.classifier.save_model()
                logging.info("Model trained and saved")

            mask = df[self.category_column].isna()
            unclassified = df[mask]
            
            for idx, row in enumerate(unclassified.iterrows()):
                # 텍스트 전처리 후 예측
                cleaned_text = TextExtension.clean_text(row[1][self.content_column])
                prediction = self.classifier.predict(cleaned_text)
                if prediction not in self.categories:
                    prediction = '알수없음'
                df.loc[row[0], self.category_column] = prediction

            excel_handler = ExcelHandler()
            excel_handler.save_excel_with_style(
                self.input_file, 
                self.output_file, 
                self.selected_sheet, 
                df
            )
            
            # 처리 완료 표시
            self.is_processing_done = True
            progress_thread.wait()

            self.finished.emit()
            
        except Exception as e:
            logging.error(f"Error during processing: {str(e)}", exc_info=True)
            self.error.emit(str(e))
            self.is_processing_done = True