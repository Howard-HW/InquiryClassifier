import logging
import os
import pandas as pd
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTextEdit, QProgressBar,
                             QDialog, QDialogButtonBox, QComboBox, QFileDialog,
                             QMessageBox, QFrame)

from core import InquiryClassifier, TrainingThread, ExcelHandler, RetrainingThread
from utils.resource_manager import ResourceManager
from utils.version_manager import VersionManager
from .dialogs import (ClassificationRulesDialog, ColumnSelectionDialog,
                      ReviewDialog, PreprocessingRulesDialog, AboutDialog)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # GUI 렌더링 최적화 설정 추가
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.classifier = InquiryClassifier()
        self.selected_sheet = None
        self.categories = []
        self.update_original = False
        self.input_file = None
        self.output_file = None
        self.initUI()
        
        # UI 초기화 후 모델 상태 확인
        has_model = self.classifier.load_model()
        if has_model:
            logging.info("Existing model loaded successfully")
            self.updateModelStatus()
    
    def initUI(self):
        self.setWindowTitle('문의 분류 프로그램')
        self.setGeometry(100, 100, 800, 600)
        self.setupIcon()
        self.setupMenuBar()  # 메뉴바 설정 추가
        self.setupMainLayout()
        logging.info("Application UI initialized")
        
    def setupIcon(self):
        try:
            if sys.platform == "darwin":  # macOS
                icon_path = ResourceManager.get_resource_path('app_icon.icns')
            elif sys.platform == "win32":  # Windows
                icon_path = ResourceManager.get_resource_path('app_icon.ico')
            else:  # Linux
                icon_path = ResourceManager.get_resource_path('app_icon.png')
                
            if icon_path and os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logging.warning(f"Could not set application icon: {str(e)}")

    def setupMenuBar(self):
        menubar = self.menuBar()
        
        # 설정 메뉴
        settings_menu = menubar.addMenu('설정')
        
        # 분류 규칙 관리
        rules_action = QAction('분류 규칙 관리', self)
        rules_action.triggered.connect(self.showClassificationRulesDialog)
        settings_menu.addAction(rules_action)
        
        # 전처리 규칙 관리
        preprocess_action = QAction('전처리 규칙 관리', self)
        preprocess_action.triggered.connect(self.showPreprocessingRulesDialog)
        settings_menu.addAction(preprocess_action)
        
        # 모델 관리 메뉴
        model_menu = menubar.addMenu('모델')
        self.export_model_action = QAction('모델 내보내기', self)
        import_model_action = QAction('모델 불러오기', self)
        self.export_model_action.triggered.connect(self.exportModel)
        import_model_action.triggered.connect(self.importModel)
        
        self.export_model_action.setEnabled(hasattr(self.classifier, 'model') and self.classifier.model is not None)
        self.export_model_action.setStatusTip('학습된 모델이 있을 때만 내보내기가 가능합니다')
        
        model_menu.addAction(self.export_model_action)
        model_menu.addAction(import_model_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말')
        
        # 프로그램 정보
        about_action = QAction('프로그램 정보', self)
        about_action.triggered.connect(self.showAboutDialog)
        help_menu.addAction(about_action)

    def showAboutDialog(self):
        """프로그램 정보 다이얼로그를 표시합니다."""
        dialog = AboutDialog(self)
        dialog.exec()

    def showPreprocessingRulesDialog(self):
        """전처리 규칙 관리 다이얼로그를 표시합니다."""
        dialog = PreprocessingRulesDialog(self)
        dialog.exec()
    
    def exportModel(self):
        if not hasattr(self.classifier, 'model') or self.classifier.model is None:
            QMessageBox.information(self, '알림', '내보낼 모델이 없습니다.\n먼저 데이터를 학습시켜 모델을 생성해주세요.')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "모델 내보내기",
            "",
            "Joblib 파일 (*.joblib)"
        )
        if file_path:
            if not file_path.endswith('.joblib'):
                file_path += '.joblib'
            try:
                current_model = {
                    'vectorizer': self.classifier.vectorizer,
                    'model': self.classifier.model
                }
                joblib.dump(current_model, file_path)
                self.log_text.append(f'모델을 성공적으로 내보냈습니다: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '에러', f'모델 내보내기 실패:\n{str(e)}')

    def importModel(self):
        """모델 불러오기"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "모델 불러오기",
                "",
                "Joblib 파일 (*.joblib)"
            )
            if file_path:
                saved_model = joblib.load(file_path)
                self.classifier.vectorizer = saved_model['vectorizer']
                self.classifier.model = saved_model['model']
                
                # 모델 파일 복사
                model_path = self.classifier.model_file
                joblib.dump(saved_model, model_path)
                
                self.log_text.append(f'모델을 성공적으로 불러왔습니다: {file_path}')
                
                # 모델 상태 업데이트
                self.updateModelStatus()
                
        except Exception as e:
            QMessageBox.critical(self, '에러', f'모델 불러오기 실패:\n{str(e)}')

    def showClassificationRulesDialog(self):
        dialog = ClassificationRulesDialog(self.classifier.rules, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.classifier.rules = dialog.rules
    
    def setupMainLayout(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # 모델 상태 표시 섹션 추가
        self.setupModelStatusSection(layout)
        self.setupInfoLabel(layout)
        self.setupFileButtons(layout)
        self.setupProgressSection(layout)
        self.setupLogSection(layout)
        self.setupActionButtons(layout)
        
        # 초기 모델 상태 업데이트
        self.updateModelStatus()

    def setupModelStatusSection(self, layout):
        """모델 상태를 표시하는 섹션을 설정합니다."""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        status_layout = QVBoxLayout()
        
        # 모델 상태 표시 레이블
        self.model_status_label = QLabel()
        self.model_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(self.model_status_label)
        
        # 모델 버전 표시 레이블
        self.model_version_label = QLabel()
        self.model_version_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(self.model_version_label)
        
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)

    def updateModelStatus(self):
        """모델 상태 정보를 업데이트합니다."""
        try:
            version_info = VersionManager.load_version_info()
            model_trained = self.classifier.is_model_trained()
            
            logging.info(f"Updating model status - Model trained: {model_trained}")
            
            if model_trained:
                self.model_status_label.setText("✓ 학습된 모델이 있습니다")
                self.model_status_label.setStyleSheet("color: green;")
                self.model_version_label.setText(f"모델 버전: {version_info.get('model_version', '알 수 없음')}")
                self.classify_btn.setEnabled(True)
                self.export_model_action.setEnabled(True)
            else:
                self.model_status_label.setText("✗ 학습된 모델이 없습니다")
                self.model_status_label.setStyleSheet("color: red;")
                self.model_version_label.setText("새로운 모델을 학습해주세요")
                self.classify_btn.setEnabled(False)
                self.export_model_action.setEnabled(False)
            
            # 프로그램 버전 정보 표시
            program_version = version_info.get('version', VersionManager.CURRENT_VERSION)
            self.setWindowTitle(f'문의 분류 프로그램 v{program_version}')
            
        except Exception as e:
            logging.error(f"Error updating model status: {str(e)}")
            self.model_status_label.setText("! 모델 상태 확인 실패")
            self.model_status_label.setStyleSheet("color: orange;")
            self.model_version_label.setText("오류가 발생했습니다")
            self.classify_btn.setEnabled(False)
            self.export_model_action.setEnabled(False)
            
        except Exception as e:
            logging.error(f"Error updating model status: {str(e)}")
            self.model_status_label.setText("! 모델 상태 확인 실패")
            self.model_status_label.setStyleSheet("color: orange;")
            self.model_version_label.setText("오류가 발생했습니다")
            self.classify_btn.setEnabled(False)
            self.export_model_action.setEnabled(False)
        
    def setupInfoLabel(self, layout):
        info_label = QLabel('문의 내용을 자동으로 분류하는 프로그램입니다.\n엑셀 파일을 선택하고 분류 방식을 선택해주세요.')
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
    def setupFileButtons(self, layout):
        file_layout = QHBoxLayout()
        
        self.input_btn = QPushButton('입력 파일 선택')
        self.input_btn.clicked.connect(self.select_input_file)
        file_layout.addWidget(self.input_btn)
        
        self.output_btn = QPushButton('출력 파일 선택')
        self.output_btn.clicked.connect(self.select_output_file)
        file_layout.addWidget(self.output_btn)
        
        layout.addLayout(file_layout)

        self.input_label = QLabel('입력 파일: 선택되지 않음')
        layout.addWidget(self.input_label)
        
        self.output_label = QLabel('출력 파일: 선택되지 않음')
        layout.addWidget(self.output_label)
        
    def setupProgressSection(self, layout):
        progress_label = QLabel('진행 상황:')
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
    def setupLogSection(self, layout):
        log_label = QLabel('처리 로그:')
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
    def setupActionButtons(self, layout):
        button_layout = QHBoxLayout()
        
        self.train_btn = QPushButton('새로 학습하고 분류하기')
        self.train_btn.clicked.connect(lambda: self.process_data(True))
        button_layout.addWidget(self.train_btn)
        
        self.classify_btn = QPushButton('기존 모델로 분류하기')
        self.classify_btn.clicked.connect(lambda: self.process_data(False))
        button_layout.addWidget(self.classify_btn)
        
        layout.addLayout(button_layout)
        
    def select_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "입력 파일 선택",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_name:
            try:
                xls = pd.ExcelFile(file_name)
                
                # 데이터 시트 선택 다이얼로그
                sheet_dialog = QDialog(self)
                sheet_dialog.setWindowTitle('시트 선택')
                layout = QVBoxLayout()
                
                sheet_combo = QComboBox()
                sheet_combo.addItems(xls.sheet_names)
                layout.addWidget(QLabel('분석할 데이터 시트를 선택하세요:'))
                layout.addWidget(sheet_combo)
                
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | 
                    QDialogButtonBox.StandardButton.Cancel
                )
                buttons.accepted.connect(sheet_dialog.accept)
                buttons.rejected.connect(sheet_dialog.reject)
                layout.addWidget(buttons)
                sheet_dialog.setLayout(layout)
                
                if sheet_dialog.exec() == QDialog.DialogCode.Accepted:
                    self.selected_sheet = sheet_combo.currentText()
                    
                    # 컬럼 선택 다이얼로그 표시
                    column_dialog = ColumnSelectionDialog(file_name, self.selected_sheet, self)
                    if column_dialog.exec() == QDialog.DialogCode.Accepted:
                        selections = column_dialog.get_selections()
                        
                        # 선택된 값들 저장
                        self.content_column = selections['content_column']
                        self.category_column = selections['result_column']
                        self.categories = selections['categories']
                        
                        self.input_file = file_name
                        self.input_label.setText(
                            f'입력 파일: {file_name}\n'
                            f'데이터 시트: {self.selected_sheet}\n'
                            f'분류 컬럼: {self.content_column} → {self.category_column}\n'
                            f'카테고리 개수: {len(self.categories)}'
                        )
                        self.log_text.append(
                            f'입력 파일이 선택되었습니다: {file_name}\n'
                            f'- 데이터 시트: {self.selected_sheet}\n'
                            f'- 내용 컬럼: {self.content_column}\n'
                            f'- 결과 컬럼: {self.category_column}\n'
                            f'- 카테고리 시트: {selections["category_sheet"]}\n'
                            f'- 카테고리 컬럼: {selections["category_column"]}\n'
                            f'- 카테고리 개수: {len(self.categories)}'
                        )
                        logging.info(f"Input file selected: {file_name}, Sheet: {self.selected_sheet}")
                    else:
                        self.reset_input_selection()
                else:
                    self.reset_input_selection()
                    
            except Exception as e:
                QMessageBox.critical(self, '에러', f'파일 로딩 중 에러가 발생했습니다:\n{str(e)}')
                self.reset_input_selection()
    
    def reset_input_selection(self):
        """입력 파일 선택 관련 변수들을 초기화합니다."""
        self.input_file = None
        self.selected_sheet = None
        self.content_column = None
        self.category_column = None
        self.categories = []
        self.input_label.setText('입력 파일: 선택되지 않음')
        logging.info("Input selection has been reset")

    def select_output_file(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('출력 옵션')
        layout = QVBoxLayout()
        
        new_file_radio = QPushButton('새 파일 생성')
        update_file_radio = QPushButton('원본 파일 업데이트')
        
        layout.addWidget(new_file_radio)
        layout.addWidget(update_file_radio)
        
        def select_new_file():
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "출력 파일 선택",
                "",
                "Excel Files (*.xlsx)"
            )
            if file_name and not file_name.endswith('.xlsx'):
                file_name += '.xlsx'
            if file_name:
                self.output_file = file_name
                self.update_original = False
                self.output_label.setText(f'출력 파일: {file_name}')
                self.log_text.append(f'출력 파일이 선택되었습니다: {file_name}')
                logging.info(f"Output file selected: {file_name}")
            dialog.accept()

        def update_original():
            self.output_file = self.input_file
            self.update_original = True
            self.output_label.setText(f'출력 파일: {self.input_file} (원본 업데이트)')
            self.log_text.append('원본 파일을 업데이트하도록 설정되었습니다.')
            logging.info("Original file will be updated")
            dialog.accept()

        new_file_radio.clicked.connect(select_new_file)
        update_file_radio.clicked.connect(update_original)
        
        dialog.setLayout(layout)
        dialog.exec()

    def process_data(self, should_train):
        if not self.input_file or not self.output_file:
            QMessageBox.warning(self, '경고', '입력 파일과 출력 파일을 모두 선택해주세요.')
            return
            
        if not hasattr(self, 'content_column') or not hasattr(self, 'category_column'):
            QMessageBox.warning(self, '경고', '분류할 컬럼을 선택해주세요.')
            return
        
        self.log_text.append('처리를 시작합니다...')
        self.progress_bar.setValue(0)
        
        self.train_btn.setEnabled(False)
        self.classify_btn.setEnabled(False)
        
        try:
            self.thread = TrainingThread(
                classifier=self.classifier,
                input_file=self.input_file,
                output_file=self.output_file,
                should_train=should_train,
                selected_sheet=self.selected_sheet,
                content_column=self.content_column,
                category_column=self.category_column,
                categories=self.categories
            )
            self.thread.progress_updated.connect(self.update_progress)
            self.thread.finished.connect(self.process_finished)
            self.thread.error.connect(self.process_error)
            self.thread.start()
        except Exception as e:
            self.process_error(str(e))

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def process_finished(self):
        """분류 작업이 완료된 후의 처리"""
        self.log_text.append('자동 분류가 완료되었습니다.')
        
        try:
            # 결과 데이터 로드
            df = pd.read_excel(self.output_file, sheet_name=self.selected_sheet)
            
            # 검수 다이얼로그 표시
            review_dialog = ReviewDialog(
                df=df,
                content_column=self.content_column,
                category_column=self.category_column,
                categories=self.categories,
                classifier=self.classifier,  # classifier 추가
                parent=self
            )
            
            if review_dialog.exec() == QDialog.DialogCode.Accepted:
                # 수정된 데이터 저장
                modified_df = review_dialog.get_modified_data()
                
                # ExcelHandler를 사용하여 저장
                excel_handler = ExcelHandler()
                excel_handler.save_excel_with_style(
                    input_file=self.input_file,
                    output_file=self.output_file,
                    sheet_name=self.selected_sheet,
                    data=modified_df,
                    is_update=(self.output_file == self.input_file)
                )
                
                self.log_text.append('검수 결과가 저장되었습니다.')
                
                # 재학습 요청이 있는 경우
                if hasattr(review_dialog, 'retrain_requested') and review_dialog.retrain_requested:
                    if hasattr(review_dialog, 'training_data'):
                        self.log_text.append('수정된 데이터로 재학습을 시작합니다...')
                        self.progress_bar.setValue(0)
                        
                        # 버튼 비활성화
                        self.train_btn.setEnabled(False)
                        self.classify_btn.setEnabled(False)
                        
                        # 재학습 스레드 시작
                        self.retrain_thread = RetrainingThread(
                            self.classifier,
                            review_dialog.training_data,
                            self.content_column,
                            self.category_column
                        )
                        self.retrain_thread.progress_updated.connect(self.update_progress)
                        self.retrain_thread.finished.connect(self.retrain_finished)
                        self.retrain_thread.error.connect(self.process_error)
                        self.retrain_thread.start()
                        return  # 재학습 시작 후 종료 (나머지는 retrain_finished에서 처리)
                    else:
                        logging.error("Training data not found in review dialog")
                        QMessageBox.warning(self, '경고', '재학습용 데이터를 찾을 수 없습니다.')
        
        except Exception as e:
            self.log_text.append(f'검수 과정 중 오류가 발생했습니다: {str(e)}')
            logging.error(f"Error during review process: {str(e)}", exc_info=True)
            QMessageBox.critical(self, '오류', f'검수 과정 중 오류가 발생했습니다:\n{str(e)}')
        
        self.finish_processing()
        
    def retrain_finished(self):
        """재학습이 완료된 후의 처리"""
        self.log_text.append('재학습이 완료되었습니다.')
        self.updateModelStatus()
        self.finish_processing()
        QMessageBox.information(self, '완료', '재학습이 완료되었습니다.')

    def finish_processing(self):
        """처리 완료 시의 공통 작업"""
        self.progress_bar.setValue(100)
        self.train_btn.setEnabled(True)
        self.classify_btn.setEnabled(True)
        self.export_model_action.setEnabled(True)

    def update_progress(self, value):
        """진행률을 업데이트합니다."""
        self.progress_bar.setValue(value)

    def process_error(self, error_msg):
        """에러 처리"""
        self.log_text.append(f'오류가 발생했습니다: {error_msg}')
        self.progress_bar.setValue(0)
        self.train_btn.setEnabled(True)
        self.classify_btn.setEnabled(True)
        QMessageBox.critical(self, '오류', f'처리 중 오류가 발생했습니다:\n{error_msg}')

        
    def process_error(self, error_msg):
        self.log_text.append(f'에러가 발생했습니다: {error_msg}')
        
        self.train_btn.setEnabled(True)
        self.classify_btn.setEnabled(True)
        
        QMessageBox.critical(self, '에러', f'처리 중 에러가 발생했습니다:\n{error_msg}')
