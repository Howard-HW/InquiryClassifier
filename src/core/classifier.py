import os
import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import json
from utils.resource_manager import ResourceManager
from utils.version_manager import VersionManager

class InquiryClassifier:
    def __init__(self, model_file='inquiry_classifier.joblib'):
        self.model_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', model_file)
        
        # 모델과 벡터라이저를 None으로 초기화
        self.model = None
        self.vectorizer = None
        
        # 버전 호환성 체크
        version_updated = VersionManager.check_version_compatibility()
        if version_updated:
            logging.info("Version updated, initializing new model")
            self.initialize_new_model()
        else:
            self.load_or_initialize_model()
        
        # 분류 규칙 로드
        self.rules = self.load_classification_rules()

    def initialize_new_model(self):
        """새로운 모델을 초기화합니다."""
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.model = None  # 학습되기 전까지는 None
        logging.info("New model initialized")
        
    def is_model_trained(self):
        """모델이 학습되었는지 확인합니다."""
        if self.model is None or self.vectorizer is None:
            return False
            
        try:
            # MultinomialNB 모델의 경우 학습된 클래스 수를 확인
            n_classes = len(self.model.classes_)
            return n_classes > 0
        except Exception as e:
            logging.error(f"Error checking model training status: {str(e)}")
            return False


    def load_or_initialize_model(self):
        """저장된 모델이 있으면 로드하고, 없으면 새로 초기화합니다."""
        if os.path.exists(self.model_file):
            try:
                self.load_model()
            except Exception as e:
                logging.error(f"Error loading model, initializing new one: {str(e)}")
                self.initialize_new_model()
        else:
            self.initialize_new_model()

    def save_model(self):
        """모델을 저장하고 버전 정보를 업데이트합니다."""
        try:
            os.makedirs(os.path.dirname(self.model_file), exist_ok=True)
            joblib.dump({
                'vectorizer': self.vectorizer,
                'model': self.model
            }, self.model_file)
            
            # 모델 버전 정보 업데이트
            version_info = VersionManager.load_version_info()
            version_info["model_version"] = VersionManager.CURRENT_VERSION
            VersionManager.save_version_info(version_info)
            
            logging.info(f"Model saved to {self.model_file} with version {VersionManager.CURRENT_VERSION}")
        except Exception as e:
            logging.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self):
        """저장된 모델을 불러옵니다."""
        try:
            if os.path.exists(self.model_file):
                saved_model = joblib.load(self.model_file)
                self.vectorizer = saved_model['vectorizer']
                self.model = saved_model['model']
                
                # 모델이 실제로 학습되었는지 확인
                if self.is_model_trained():
                    logging.info(f"Trained model loaded from {self.model_file}")
                    return True
                else:
                    logging.info("Loaded model is not trained")
                    return False
            else:
                logging.info("No existing model file found")
                return False
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            self.model = None
            self.vectorizer = None
            return False

    def load_classification_rules(self):
        try:
            rules_path = ResourceManager.get_resource_path('classification_rules.json')
            if rules_path and os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logging.warning("Classification rules file not found.")
                return {"version": "1.0", "rules": {"keyword_based": {}, "pattern_based": {}}}
        except Exception as e:
            logging.error(f"Error loading classification rules: {str(e)}")
            return {"version": "1.0", "rules": {"keyword_based": {}, "pattern_based": {}}}
        
    def save_model(self):
        """모델 저장"""
        try:
            joblib.dump({
                'vectorizer': self.vectorizer,
                'model': self.model
            }, self.model_file)
            logging.info(f"Model saved to {self.model_file}")
        except Exception as e:
            logging.error(f"Error saving model: {str(e)}")
            raise

    def preprocess_text(self, text):
        """텍스트 전처리"""
        if isinstance(text, str):
            return text.lower().strip()
        return ""

    def train(self, texts, labels):
        """모델 학습"""
        try:
            processed_texts = [self.preprocess_text(text) for text in texts]
            X = self.vectorizer.fit_transform(processed_texts)
            self.model = MultinomialNB()
            self.model.fit(X, labels)
            logging.info("Model training completed")
        except Exception as e:
            logging.error(f"Error during training: {str(e)}")
            self.model = None  # 학습 실패 시 모델을 None으로 설정
            raise

    def predict(self, text):
        try:
            processed_text = self.preprocess_text(text).lower()
            
            # 키워드 기반 체크
            keyword_rules = self.rules.get('rules', {}).get('keyword_based', {})
            for category, keywords in keyword_rules.items():
                if any(keyword.lower() in processed_text for keyword in keywords):
                    return category
            
            # ML 모델 사용
            text_tfidf = self.vectorizer.transform([processed_text])
            return self.model.predict(text_tfidf)[0]
            
        except Exception as e:
            logging.error(f"Error during prediction: {str(e)}")
            return self.rules.get('rules', {}).get('default_category', '알수없음')

def process_file(self, input_file, output_file, content_column, category_column, should_train=False, progress_callback=None):
    """파일 처리 - 사용자가 선택한 컬럼 사용"""
    try:
        df = pd.read_excel(input_file, encoding='utf-8')
        
        if should_train:
            train_data = df[df[category_column].notna()]
            self.train(train_data[content_column], train_data[category_column])
            self.save_model()

        mask = df[category_column].isna()
        unclassified = df[mask]
        
        total = len(unclassified)
        for idx, row in enumerate(unclassified.iterrows()):
            prediction = self.predict(row[1][content_column])
            df.loc[row[0], category_column] = prediction
            
            if progress_callback and total > 0:
                progress = int((idx + 1) / total * 100)
                progress_callback(progress)

        df.to_excel(output_file, index=False, encoding='utf-8-sig')
        logging.info(f"File processing completed: {output_file}")
        
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        raise