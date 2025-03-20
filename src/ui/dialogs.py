from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox,
                        QDialogButtonBox, QRadioButton, QFileDialog,
                        QMessageBox, QTableWidget, QTextEdit,
                        QTableWidgetItem, QWidget, QHBoxLayout, QPushButton,
                        QGroupBox, QFormLayout, QListWidget, QListWidgetItem,  # QListWidgetItem 추가
                        QLineEdit, QScrollArea, QFrame, QCheckBox) 
from PyQt6.QtCore import QTimer, Qt
from utils.resource_manager import ResourceManager
from utils.version_manager import VersionManager
import pandas as pd
import logging
import json
import os

class SheetSelectionDialog(QDialog):
    def __init__(self, file_name, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.selected_sheet = None
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle('시트 선택')
        layout = QVBoxLayout()
        
        try:
            xls = pd.ExcelFile(self.file_name)
            self.combo = QComboBox()
            self.combo.addItems(xls.sheet_names)
            
            layout.addWidget(QLabel('분석할 시트를 선택하세요:'))
            layout.addWidget(self.combo)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | 
                QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)
            
            self.setLayout(layout)
            
        except Exception as e:
            logging.error(f"Error loading Excel file: {str(e)}")
            self.reject()
            
    def get_selected_sheet(self):
        return self.combo.currentText()

class OutputSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_file = None
        self.update_original = False
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle('출력 옵션')
        layout = QVBoxLayout()
        
        self.new_file_radio = QRadioButton('새 파일 생성')
        self.update_original_radio = QRadioButton('원본 파일 업데이트')
        self.new_file_radio.setChecked(True)
        
        layout.addWidget(self.new_file_radio)
        layout.addWidget(self.update_original_radio)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_handler)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def accept_handler(self):
        if self.new_file_radio.isChecked():
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "출력 파일 선택",
                "",
                "Excel Files (*.xlsx)"
            )
            if file_name:
                if not file_name.endswith('.xlsx'):
                    file_name += '.xlsx'
                self.output_file = file_name
                self.update_original = False
                self.accept()
        else:
            self.update_original = True
            self.accept()
    
    def get_output_info(self):
        return {
            'file_path': self.output_file,
            'update_original': self.update_original
        }

class ClassificationRulesDialog(QDialog):
    def __init__(self, rules, parent=None):
        super().__init__(parent)
        self.rules = rules.copy()
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle('분류 규칙 관리')
        layout = QVBoxLayout()
        
        # 파일 관리 버튼 추가
        file_btn_layout = QHBoxLayout()
        export_btn = QPushButton('규칙 내보내기')
        import_btn = QPushButton('규칙 불러오기')
        export_btn.clicked.connect(self.exportRules)
        import_btn.clicked.connect(self.importRules)
        file_btn_layout.addWidget(export_btn)
        file_btn_layout.addWidget(import_btn)
        layout.addLayout(file_btn_layout)
        
        # 탭 위젯 생성
        tabs = QTabWidget()
        
        # 키워드 기반 규칙 탭
        keyword_tab = QWidget()
        keyword_layout = QVBoxLayout()
        
        # 키워드 규칙 테이블
        self.keyword_table = QTableWidget()
        self.keyword_table.setColumnCount(2)
        self.keyword_table.setHorizontalHeaderLabels(['분류', '키워드 (쉼표로 구분)'])
        self.updateKeywordTable()
        keyword_layout.addWidget(self.keyword_table)
        
        # 키워드 규칙 버튼
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('추가')
        add_btn.clicked.connect(self.addKeywordRule)
        remove_btn = QPushButton('삭제')
        remove_btn.clicked.connect(self.removeKeywordRule)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        keyword_layout.addLayout(btn_layout)
        
        keyword_tab.setLayout(keyword_layout)
        tabs.addTab(keyword_tab, "키워드 기반 규칙")
        
        # 패턴 기반 규칙 탭 (향후 확장)
        pattern_tab = QWidget()
        pattern_layout = QVBoxLayout()
        pattern_layout.addWidget(QLabel('패턴 기반 규칙은 향후 지원 예정입니다.'))
        pattern_tab.setLayout(pattern_layout)
        tabs.addTab(pattern_tab, "패턴 기반 규칙")
        
        layout.addWidget(tabs)
        
        # 저장/취소 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.saveRules)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def exportRules(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "규칙 내보내기",
            "",
            "JSON 파일 (*.json)"
        )
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.rules, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, '성공', '규칙을 성공적으로 내보냈습니다.')
            except Exception as e:
                QMessageBox.critical(self, '에러', f'규칙 내보내기 실패:\n{str(e)}')
    
    def importRules(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "규칙 불러오기",
            "",
            "JSON 파일 (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_rules = json.load(f)
                self.rules = new_rules
                self.updateKeywordTable()
                QMessageBox.information(self, '성공', '규칙을 성공적으로 불러왔습니다.')
            except Exception as e:
                QMessageBox.critical(self, '에러', f'규칙 불러오기 실패:\n{str(e)}')
        
    def updateKeywordTable(self):
        keyword_rules = self.rules.get('rules', {}).get('keyword_based', {})
        self.keyword_table.setRowCount(len(keyword_rules))
        for i, (category, keywords) in enumerate(keyword_rules.items()):
            self.keyword_table.setItem(i, 0, QTableWidgetItem(category))
            self.keyword_table.setItem(i, 1, QTableWidgetItem(','.join(keywords)))
    
    def addKeywordRule(self):
        self.keyword_table.setRowCount(self.keyword_table.rowCount() + 1)
    
    def removeKeywordRule(self):
        current_row = self.keyword_table.currentRow()
        if current_row >= 0:
            self.keyword_table.removeRow(current_row)
    
    def saveRules(self):
        try:
            # 키워드 규칙 수집
            keyword_rules = {}
            for i in range(self.keyword_table.rowCount()):
                category = self.keyword_table.item(i, 0)
                keywords = self.keyword_table.item(i, 1)
                if category and keywords and category.text().strip():
                    keyword_rules[category.text().strip()] = [
                        k.strip() for k in keywords.text().split(',')
                        if k.strip()
                    ]
            
            # 전체 규칙 구조 업데이트
            self.rules['rules']['keyword_based'] = keyword_rules
            
            # 파일 저장
            rules_path = ResourceManager.get_resource_path('classification_rules.json')
            with open(rules_path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, '에러', f'규칙 저장 중 오류 발생:\n{str(e)}')

class ColumnSelectionDialog(QDialog):
    def __init__(self, file_path, sheet_name, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.data_sheet = sheet_name
        self.columns = None
        self.categories = []
        self.setupUI()
        
        # UI 설정 완료 후 데이터 로드 및 시그널 연결
        self.initializeData()
        
    def setupUI(self):
        """UI 컴포넌트들을 생성하고 배치합니다."""
        self.setWindowTitle('데이터 설정')
        self.setMinimumWidth(500)
        main_layout = QVBoxLayout()
        
        try:
            # 데이터 시트 설정
            data_group = QGroupBox("데이터 시트 설정")
            data_layout = QFormLayout()
            
            # 데이터 시트의 컬럼 로드
            df = pd.read_excel(self.file_path, sheet_name=self.data_sheet)
            self.columns = df.columns.tolist()
            logging.info(f"Found columns: {self.columns}")
            
            self.content_combo = QComboBox()
            self.content_combo.addItems(self.columns)
            if "질문내용" in self.columns:
                self.content_combo.setCurrentText("질문내용")
                
            self.category_result_combo = QComboBox()
            self.category_result_combo.addItems(self.columns)
            if "분류" in self.columns:
                self.category_result_combo.setCurrentText("분류")
                
            data_layout.addRow('분류할 내용 컬럼:', self.content_combo)
            data_layout.addRow('분류 결과 컬럼:', self.category_result_combo)
            data_group.setLayout(data_layout)
            main_layout.addWidget(data_group)
            
            # 카테고리 설정
            category_group = QGroupBox("카테고리 설정")
            category_layout = QFormLayout()
            
            xls = pd.ExcelFile(self.file_path)
            sheets = xls.sheet_names
            logging.info(f"Available sheets: {sheets}")
            
            self.category_sheet_combo = QComboBox()
            self.category_sheet_combo.addItems(sheets)
            
            self.category_column_combo = QComboBox()
            
            category_layout.addRow('카테고리 시트:', self.category_sheet_combo)
            category_layout.addRow('카테고리 컬럼:', self.category_column_combo)
            category_group.setLayout(category_layout)
            main_layout.addWidget(category_group)
            
            # 미리보기 섹션
            preview_group = QGroupBox("카테고리 미리보기")
            preview_layout = QVBoxLayout()
            self.preview_list = QListWidget()
            self.preview_list.setMinimumHeight(200)
            preview_layout.addWidget(self.preview_list)
            preview_group.setLayout(preview_layout)
            main_layout.addWidget(preview_group)
            
            # 버튼
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | 
                QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.validate_and_accept)
            buttons.rejected.connect(self.reject)
            main_layout.addWidget(buttons)
            
            self.setLayout(main_layout)
            
            # 모든 UI 컴포넌트가 생성된 후에 초기값 설정 및 시그널 연결
            if "Category" in sheets:
                self.category_sheet_combo.setCurrentText("Category")
                logging.info("Selected 'Category' sheet")
                
            # 시그널 연결
            logging.info("Connecting signals")
            self.category_sheet_combo.currentTextChanged.connect(self.update_category_columns)
            self.category_column_combo.currentTextChanged.connect(self.update_preview)
            
            # 초기 데이터 로드 - 약간의 지연을 주어 UI가 완전히 준비된 후 실행
            QTimer.singleShot(100, self.update_category_columns)
            
        except Exception as e:
            logging.error(f"Error in setupUI: {str(e)}", exc_info=True)
            QMessageBox.critical(self, '오류', f'UI 초기화 중 오류가 발생했습니다:\n{str(e)}')
        
    def initializeData(self):
        """데이터를 로드하고 UI를 초기화합니다."""
        try:
            # 데이터 시트의 컬럼 로드
            logging.info(f"Loading data sheet: {self.data_sheet}")
            df = pd.read_excel(self.file_path, sheet_name=self.data_sheet)
            self.columns = df.columns.tolist()
            logging.info(f"Found columns: {self.columns}")
            
            # 컬럼 콤보박스 초기화
            self.content_combo.addItems(self.columns)
            self.category_result_combo.addItems(self.columns)
            
            # 기본값 설정
            if "질문내용" in self.columns:
                self.content_combo.setCurrentText("질문내용")
            if "분류" in self.columns:
                self.category_result_combo.setCurrentText("분류")
            
            # 시트 목록 로드
            xls = pd.ExcelFile(self.file_path)
            sheets = xls.sheet_names
            logging.info(f"Available sheets: {sheets}")
            self.category_sheet_combo.addItems(sheets)
            
            # Category 시트가 있으면 선택
            if "Category" in sheets:
                self.category_sheet_combo.setCurrentText("Category")
                logging.info("Selected 'Category' sheet")
            
            # 시그널 연결
            logging.info("Connecting signals")
            self.category_sheet_combo.currentTextChanged.connect(self.update_category_columns)
            self.category_column_combo.currentTextChanged.connect(self.update_preview)
            
            # 초기 카테고리 컬럼 목록 로드
            logging.info("Initial update of category columns")
            self.update_category_columns()
            
        except Exception as e:
            logging.error(f"Error in initializeData: {str(e)}", exc_info=True)
            QMessageBox.critical(self, '오류', f'데이터 초기화 중 오류가 발생했습니다:\n{str(e)}')
            
            
    def update_category_columns(self):
        """선택된 카테고리 시트의 컬럼 목록을 업데이트합니다."""
        try:
            sheet_name = self.category_sheet_combo.currentText()
            logging.info(f"Loading columns from sheet: {sheet_name}")
            
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            columns = df.columns.tolist()
            
            current_text = self.category_column_combo.currentText()
            self.category_column_combo.clear()
            self.category_column_combo.addItems(columns)
            
            # 이전 선택 유지 또는 기본값 설정
            if "분류3" in columns:
                self.category_column_combo.setCurrentText("분류3")
                logging.info("Selected '분류3' column")
            elif current_text and current_text in columns:
                self.category_column_combo.setCurrentText(current_text)
            
            self.update_preview()
            
        except Exception as e:
            logging.error(f"Error updating category columns: {str(e)}", exc_info=True)
            QMessageBox.warning(self, '오류', '카테고리 시트 로딩 중 오류가 발생했습니다.')

    def update_preview(self):
        """선택된 카테고리 컬럼의 고유값들을 미리보기에 표시합니다."""
        try:
            sheet_name = self.category_sheet_combo.currentText()
            column_name = self.category_column_combo.currentText()
            
            logging.info(f"Updating preview for sheet: {sheet_name}, column: {column_name}")
            
            if sheet_name and column_name:
                df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                if column_name in df.columns:
                    self.categories = df[column_name].dropna().unique().tolist()
                    self.categories.sort()  # 카테고리 정렬
                    logging.info(f"Found {len(self.categories)} unique categories")
                    
                    self.preview_list.clear()
                    for category in self.categories:
                        item = str(category).strip()
                        if item:  # 빈 문자열이 아닌 경우만 추가
                            self.preview_list.addItem(item)
                            logging.debug(f"Added category: {item}")
                    
                    logging.info("Preview list updated successfully")
                else:
                    logging.warning(f"Column {column_name} not found in sheet {sheet_name}")
        except Exception as e:
            logging.error(f"Error updating preview: {str(e)}", exc_info=True)
            self.preview_list.clear()
            self.preview_list.addItem("카테고리 로딩 중 오류 발생")
    
    def validate_and_accept(self):
        """선택된 값들을 검증하고 다이얼로그를 승인합니다."""
        if not self.categories:
            QMessageBox.warning(self, '경고', '유효한 카테고리가 없습니다.\n카테고리 설정을 확인해주세요.')
            return
            
        if self.content_combo.currentText() == self.category_result_combo.currentText():
            QMessageBox.warning(self, '경고', '분류할 내용 컬럼과 분류 결과 컬럼이 같을 수 없습니다.')
            return
            
        self.accept()
    
    def get_selections(self):
        """사용자가 선택한 값들을 반환합니다."""
        return {
            'content_column': self.content_combo.currentText(),
            'result_column': self.category_result_combo.currentText(),
            'category_sheet': self.category_sheet_combo.currentText(),
            'category_column': self.category_column_combo.currentText(),
            'categories': self.categories
        }

class ReviewDialog(QDialog):
    def __init__(self, df, content_column, category_column, categories, classifier, parent=None):
        super().__init__(parent)
        self.df = df.copy()
        self.content_column = content_column
        self.category_column = category_column
        self.categories = categories
        self.classifier = classifier  # classifier 저장
        self.modified_rows = {}
        
        # 원본 데이터와 신규 분류 데이터를 구분
        self.new_classifications = None
        self.filter_new_classifications()
        
        self.setupUI()
        
    def filter_new_classifications(self):
        """신규 분류된 항목만 필터링합니다."""
        try:
            # 기존 분류가 있던 행은 제외
            original_df = pd.read_excel(self.parent().input_file, sheet_name=self.parent().selected_sheet)
            original_classifications = original_df[self.category_column].notna()
            original_indices = set(original_df[original_classifications].index)
            
            # 현재 분류가 있는 행 중에서 기존에 없던 것만 선택
            current_classifications = self.df[self.category_column].notna()
            all_current_indices = set(self.df[current_classifications].index)
            
            # 신규 분류된 인덱스 = 현재 분류된 것 - 원본에 있던 것
            new_indices = all_current_indices - original_indices
            
            # 신규 분류된 데이터만 선택
            self.new_classifications = self.df.loc[list(new_indices)].copy()
            
            logging.info(f"Found {len(self.new_classifications)} newly classified items")
            
        except Exception as e:
            logging.error(f"Error filtering new classifications: {str(e)}")
            self.new_classifications = self.df.copy()
        
    def setupUI(self):
        self.setWindowTitle('신규 분류 결과 검수')
        self.setMinimumSize(1200, 800)  # 다이얼로그 크기 증가
        layout = QVBoxLayout()
        
        # 상단 정보 표시
        total_count = len(self.new_classifications)
        info_label = QLabel(f'신규 분류된 {total_count}건을 검수합니다.')
        layout.addWidget(info_label)
        
        # 검색 기능
        search_layout = QHBoxLayout()
        
        # 검색 타입 선택
        self.search_type = QComboBox()
        self.search_type.addItems(['내용', '분류결과'])
        search_layout.addWidget(self.search_type)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('검색어 입력...')
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # 메인 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # 컬럼 수 증가
        self.table.setHorizontalHeaderLabels([
            '내용', 
            '자동 분류 결과', 
            '검수',
            '수정',
            '최종 분류'
        ])
        
        # 테이블 스타일 설정
        self.table.setWordWrap(True)  # 자동 줄바꿈 활성화
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)  # 텍스트 생략 비활성화
        self.table.verticalHeader().setDefaultSectionSize(80)  # 행 높이 설정
        
        # 컬럼 너비 설정
        table_width = 1160  # 여백 고려
        self.table.setColumnWidth(0, int(table_width * 0.5))  # 내용 컬럼 (50%)
        self.table.setColumnWidth(1, int(table_width * 0.2))  # 자동 분류 결과 (20%)
        self.table.setColumnWidth(2, int(table_width * 0.1))  # 수정 버튼 (10%)
        self.table.setColumnWidth(3, int(table_width * 0.2))  # 최종 분류 (20%)
        
        self.setupTableContent()
        layout.addWidget(self.table)
        
        # 통계 정보
        stats_group = QGroupBox("검수 현황")
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel()
        self.updateStats()
        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        save_button = QPushButton('저장 후 닫기')
        save_button.clicked.connect(self.accept)
        
        retrain_button = QPushButton('저장 및 재학습')
        retrain_button.clicked.connect(self.save_and_retrain)
        
        cancel_button = QPushButton('취소')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(retrain_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def setupTableContent(self):
        """테이블에 신규 분류 데이터를 표시합니다."""
        self.table.setRowCount(len(self.new_classifications))
        
        for row, (idx, data) in enumerate(self.new_classifications.iterrows()):
            # 내용 컬럼
            content_item = QTableWidgetItem(str(data[self.content_column]))
            content_item.setFlags(content_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            content_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 0, content_item)
            
            # 자동 분류 결과
            auto_category = str(data[self.category_column])
            category_item = QTableWidgetItem(auto_category)
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            category_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 1, category_item)
            
            # 검수 체크박스
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox = QCheckBox()
            checkbox.setProperty('row_index', row)  # 행 인덱스 저장
            checkbox.setProperty('original_idx', idx)  # 원본 인덱스 저장
            checkbox.stateChanged.connect(self.onCheckboxChanged)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 2, checkbox_widget)
            
            # 수정 버튼
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            edit_button = QPushButton('수정')
            edit_button.setEnabled(False)  # 초기에는 비활성화
            edit_button.clicked.connect(lambda checked, row=row, idx=idx: self.editCategory(row, idx))
            button_layout.addWidget(edit_button)
            button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            button_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 3, button_widget)
            
            # 최종 분류 (수정 가능)
            final_category = QTableWidgetItem(auto_category)
            final_category.setFlags(final_category.flags() & ~Qt.ItemFlag.ItemIsEditable)
            final_category.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 4, final_category)
            
            # 행 높이 자동 조정
            self.table.resizeRowToContents(row)
    
    def onCheckboxChanged(self, state):
        """체크박스 상태 변경 시 처리"""
        checkbox = self.sender()
        row = checkbox.property('row_index')
        # 수정 버튼 활성화/비활성화
        button_widget = self.table.cellWidget(row, 3)
        edit_button = button_widget.layout().itemAt(0).widget()
        edit_button.setEnabled(state == Qt.CheckState.Checked.value)
    
    def filter_items(self):
        """검색 조건에 따라 항목을 필터링합니다."""
        search_text = self.search_input.text().lower()
        search_column = 0 if self.search_type.currentText() == '내용' else 1
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, search_column)
            if item:
                text = item.text().lower()
                self.table.setRowHidden(row, search_text not in text)
        
    def editCategory(self, row, original_idx):
        """카테고리 수정 다이얼로그를 표시합니다."""
        dialog = QDialog(self)
        dialog.setWindowTitle('카테고리 수정')
        dialog.setMinimumWidth(800)  # 더 넓게 설정
        layout = QVBoxLayout()
        
        # 내용 표시
        content = self.table.item(row, 0).text()
        content_label = QLabel("내용:")
        layout.addWidget(content_label)
        
        content_text = QTextEdit()
        content_text.setPlainText(content)
        content_text.setReadOnly(True)
        content_text.setMinimumHeight(100)
        layout.addWidget(content_text)
        
        # 추천 카테고리 표시
        recommendations = self.get_category_recommendations(content)
        rec_label = QLabel("추천 카테고리:")
        layout.addWidget(rec_label)
        
        rec_list = QListWidget()
        for category, score in recommendations:
            item = QListWidgetItem(f"{category} ({score:.1f}%)")
            rec_list.addItem(item)
        rec_list.setMinimumHeight(150)
        layout.addWidget(rec_list)
        
        # 최종 선택 콤보박스
        category_label = QLabel("카테고리 선택:")
        layout.addWidget(category_label)
        
        category_combo = QComboBox()
        category_combo.addItems(sorted(self.categories))
        current_category = self.table.item(row, 4).text()
        if current_category in self.categories:
            category_combo.setCurrentText(current_category)
        layout.addWidget(category_combo)
        
        # 추천 리스트 선택 시 콤보박스에 반영
        rec_list.itemClicked.connect(
            lambda item: category_combo.setCurrentText(item.text().split(' (')[0])
        )
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_category = category_combo.currentText()
            self.table.item(row, 4).setText(new_category)
            self.modified_rows[original_idx] = new_category
            self.updateStats()
    
    def get_category_recommendations(self, content):
        """내용을 바탕으로 카테고리 추천"""
        try:
            if not hasattr(self, 'classifier') or self.classifier is None:
                logging.error("Classifier not available")
                return [("알수없음", 100.0)]

            # 벡터화
            content_vector = self.classifier.vectorizer.transform([content])
            
            # 각 카테고리별 확률 계산
            probabilities = self.classifier.model.predict_proba(content_vector)[0]
            categories = self.classifier.model.classes_
            
            # 확률이 높은 순으로 정렬
            recommendations = sorted(
                [(cat, prob * 100) for cat, prob in zip(categories, probabilities)],
                key=lambda x: x[1],
                reverse=True
            )
            
            # 상위 5개만 반환
            return recommendations[:5]
            
        except Exception as e:
            logging.error(f"Error getting recommendations: {str(e)}")
            return [("알수없음", 100.0)]
            
    def filter_items(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            content = self.table.item(row, 0).text().lower()
            self.table.setRowHidden(row, search_text not in content)
    
    def updateStats(self):
        """통계 정보를 업데이트합니다."""
        total = self.table.rowCount()
        modified = len(self.modified_rows)
        completion_rate = (modified/total*100) if total > 0 else 0.0
        
        stats_text = f"""
        전체 신규 분류: {total:,}건
        검수 완료: {modified:,}건 ({completion_rate:.1f}% 완료)
        미검수: {total-modified:,}건
        """
        self.stats_label.setText(stats_text)
        

    def get_modified_data(self):
        """수정된 데이터가 반영된 전체 DataFrame을 반환합니다."""
        modified_df = self.df.copy()
        for idx, new_category in self.modified_rows.items():
            modified_df.loc[idx, self.category_column] = new_category
        return modified_df
    
    def save_and_retrain(self):
        """수정된 내용을 저장하고 재학습을 진행합니다."""
        try:
            modified_df = self.get_modified_data()
            
            # 기존 분류 데이터와 수정된 데이터를 합침
            train_data = modified_df[modified_df[self.category_column].notna()]
            logging.info(f"Training data size: {len(train_data)}")
            logging.info(f"Categories in training data: {train_data[self.category_column].unique()}")
            logging.info(f"Modified rows: {len(self.modified_rows)}")
            
            # 검증: 모든 카테고리가 유효한지 확인
            invalid_categories = set(train_data[self.category_column]) - set(self.categories)
            if invalid_categories:
                raise ValueError(f"Invalid categories found: {invalid_categories}")
                
            self.retrain_requested = True
            self.training_data = train_data  # 재학습에 사용될 데이터 저장
            self.accept()
            
        except Exception as e:
            logging.error(f"Error preparing data for retraining: {str(e)}", exc_info=True)
            QMessageBox.critical(self, '오류', f'재학습 준비 중 오류가 발생했습니다:\n{str(e)}')
    
    def get_modified_data(self):
        """수정된 데이터를 DataFrame으로 반환합니다."""
        try:
            modified_df = self.df.copy()
            
            # 수정된 행들을 업데이트
            for idx, new_category in self.modified_rows.items():
                modified_df.loc[idx, self.category_column] = new_category
                logging.info(f"Updated row {idx} with category: {new_category}")
            
            return modified_df
            
        except Exception as e:
            logging.error(f"Error getting modified data: {str(e)}", exc_info=True)
            raise

class PreprocessingRulesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = self.load_rules()
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle('전처리 규칙 관리')
        self.setMinimumWidth(600)
        layout = QVBoxLayout()
        
        # 설명 레이블
        info_label = QLabel("텍스트 전처리 규칙을 관리합니다.")
        layout.addWidget(info_label)
        
        # 규칙 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['패턴', '대소문자 구분', '활성화', '설명'])
        self.setupTableContent()
        layout.addWidget(self.table)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton('규칙 추가')
        add_btn.clicked.connect(self.add_rule)
        
        remove_btn = QPushButton('규칙 삭제')
        remove_btn.clicked.connect(self.remove_rule)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        layout.addLayout(button_layout)
        
        # 테스트 영역
        test_group = QGroupBox("규칙 테스트")
        test_layout = QVBoxLayout()
        
        self.test_input = QTextEdit()
        self.test_input.setPlaceholderText("테스트할 텍스트를 입력하세요...")
        test_layout.addWidget(self.test_input)
        
        test_btn = QPushButton('테스트')
        test_btn.clicked.connect(self.test_rules)
        test_layout.addWidget(test_btn)
        
        self.test_output = QTextEdit()
        self.test_output.setReadOnly(True)
        test_layout.addWidget(self.test_output)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # 확인/취소 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_rules)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def setupTableContent(self):
        cut_after_rules = self.rules.get("text_preprocessing", {}).get("cut_after_strings", [])
        self.table.setRowCount(len(cut_after_rules))
        
        for row, rule in enumerate(cut_after_rules):
            # 패턴
            pattern_item = QTableWidgetItem(rule["pattern"])
            self.table.setItem(row, 0, pattern_item)
            
            # 대소문자 구분
            case_sensitive = QTableWidgetItem()
            case_sensitive.setCheckState(Qt.CheckState.Checked if rule["case_sensitive"] else Qt.CheckState.Unchecked)
            self.table.setItem(row, 1, case_sensitive)
            
            # 활성화
            enabled = QTableWidgetItem()
            enabled.setCheckState(Qt.CheckState.Checked if rule["enabled"] else Qt.CheckState.Unchecked)
            self.table.setItem(row, 2, enabled)
            
            # 설명
            description_item = QTableWidgetItem(rule["description"])
            self.table.setItem(row, 3, description_item)
        
        self.table.resizeColumnsToContents()
    
    def add_rule(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 기본값으로 새 규칙 추가
        self.table.setItem(row, 0, QTableWidgetItem(""))
        
        case_sensitive = QTableWidgetItem()
        case_sensitive.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 1, case_sensitive)
        
        enabled = QTableWidgetItem()
        enabled.setCheckState(Qt.CheckState.Checked)
        self.table.setItem(row, 2, enabled)
        
        self.table.setItem(row, 3, QTableWidgetItem(""))
    
    def remove_rule(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
    
    def test_rules(self):
        """현재 규칙을 테스트 텍스트에 적용합니다."""
        input_text = self.test_input.toPlainText()
        if not input_text:
            return
            
        # 임시 규칙 생성
        temp_rules = self.get_current_rules()
        
        # 전처리 적용
        processed_text = self.apply_rules(input_text, temp_rules)
        
        # 결과 표시
        self.test_output.setPlainText(processed_text)
    
    def get_current_rules(self):
        """현재 테이블의 내용을 규칙으로 변환합니다."""
        rules = {"text_preprocessing": {"cut_after_strings": []}}
        
        for row in range(self.table.rowCount()):
            pattern = self.table.item(row, 0).text()
            case_sensitive = self.table.item(row, 1).checkState() == Qt.CheckState.Checked
            enabled = self.table.item(row, 2).checkState() == Qt.CheckState.Checked
            description = self.table.item(row, 3).text()
            
            if pattern:  # 패턴이 비어있지 않은 경우만 추가
                rules["text_preprocessing"]["cut_after_strings"].append({
                    "pattern": pattern,
                    "case_sensitive": case_sensitive,
                    "enabled": enabled,
                    "description": description
                })
        
        return rules
    
    def apply_rules(self, text, rules):
        """규칙을 텍스트에 적용합니다."""
        if not isinstance(text, str):
            return str(text)
            
        result = text
        for rule in rules["text_preprocessing"]["cut_after_strings"]:
            if rule["enabled"]:
                pattern = rule["pattern"]
                if not rule["case_sensitive"]:
                    idx = result.lower().find(pattern.lower())
                    if idx >= 0:
                        result = result[:idx]
                else:
                    idx = result.find(pattern)
                    if idx >= 0:
                        result = result[:idx]
        
        return result.strip()
    
    def load_rules(self):
        """규칙 파일을 로드합니다."""
        try:
            rules_path = ResourceManager.get_resource_path('preprocessing_rules.json')
            if rules_path and os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logging.warning("Preprocessing rules file not found, using default rules")
                return {
                    "text_preprocessing": {
                        "cut_after_strings": [
                            {
                                "pattern": "os:",
                                "case_sensitive": False,
                                "enabled": True,
                                "description": "OS 정보 이후 텍스트 제거"
                            },
                            {
                                "pattern": "문의경로:",
                                "case_sensitive": True,
                                "enabled": True,
                                "description": "문의경로 정보 이후 텍스트 제거"
                            }
                        ]
                    }
                }
        except Exception as e:
            logging.error(f"Error loading preprocessing rules: {str(e)}")
            return {"text_preprocessing": {"cut_after_strings": []}}
    
    def save_rules(self):
        """현재 규칙을 파일로 저장합니다."""
        try:
            rules = self.get_current_rules()
            rules_path = ResourceManager.get_resource_path('preprocessing_rules.json')
            
            if not rules_path:
                raise ValueError("Cannot resolve rules file path")
                
            with open(rules_path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'규칙 저장 중 오류 발생:\n{str(e)}')

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        version_info = VersionManager.load_version_info()
        self.current_version = version_info.get('version', VersionManager.CURRENT_VERSION)
        self.setupUI()
        
    def loadDescription(self):
        """about.html 파일에서 설명 내용을 로드합니다."""
        try:
            about_path = ResourceManager.get_resource_path('about.html')
            if about_path and os.path.exists(about_path):
                with open(about_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logging.error("About file not found")
                return "<p>프로그램 설명을 불러올 수 없습니다.</p>"
        except Exception as e:
            logging.error(f"Error loading about content: {str(e)}")
            return f"<p>오류: 프로그램 설명을 불러올 수 없습니다.</p>"
        
    def setupUI(self):
        self.setWindowTitle('프로그램 정보')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        layout = QVBoxLayout()
        
        # 스크롤 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # 프로그램 제목
        title_label = QLabel("문의 분류 프로그램")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2C3E50;
                padding: 10px;
            }
        """)
        scroll_layout.addWidget(title_label)
        
        # 버전 정보
        version_label = QLabel(f"버전: {self.current_version}")
        version_label.setStyleSheet("padding: 5px;")
        scroll_layout.addWidget(version_label)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        scroll_layout.addWidget(line)
        
        # 프로그램 설명 (HTML 파일에서 로드)
        desc_label = QLabel(self.loadDescription())
        desc_label.setWordWrap(True)
        desc_label.setTextFormat(Qt.TextFormat.RichText)
        desc_label.setStyleSheet("""
            QLabel {
                line-height: 150%;
                padding: 10px;
            }
        """)
        scroll_layout.addWidget(desc_label)
        
        # 스크롤 영역에 위젯 설정
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # 닫기 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)