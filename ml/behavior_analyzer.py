import os
import pickle

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from ml.feature_extractor import analyze_url, extract_features_array

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model_data', 'behavior_model.pkl')


class BehaviorAnalyzer:
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                data = pickle.load(f)
                self.isolation_forest = data['isolation_forest']
                self.rf_classifier = data['rf_classifier']
                self.scaler = data['scaler']
                self.is_trained = True

    def _save_model(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(
                {
                    'isolation_forest': self.isolation_forest,
                    'rf_classifier': self.rf_classifier,
                    'scaler': self.scaler,
                },
                f,
            )

    def analyze_url(self, url):
        return analyze_url(url)

    def extract_features(self, activity_data):
        arr, _ = extract_features_array(activity_data)
        return arr

    def analyze(self, activity_data, user_id):
        features, _ = extract_features_array(activity_data)
        result = {
            'is_suspicious': False,
            'threat_type': None,
            'severity_level': None,
            'confidence': 0.0,
            'description': '',
            'reasons': [],
        }

        failed = int(activity_data.get('failed_attempts', 0))
        url_score = analyze_url(activity_data.get('url_address', ''))
        typing_speed = float(activity_data.get('typing_speed', 5.0))
        login_hour = int(activity_data.get('login_hour', 12))

        reasons = []
        suspicion_score = 0.0

        if failed >= 3:
            reasons.append(f'محاولات دخول فاشلة متكررة: {failed} مرات')
            suspicion_score += 0.4

        if url_score > 0.4:
            reasons.append(f'رابط مشبوه بدرجة {round(url_score * 100)}%')
            suspicion_score += url_score * 0.3

        if typing_speed < 1.0 or typing_speed > 20.0:
            reasons.append(f'سرعة كتابة غير طبيعية: {round(typing_speed, 1)} حرف/ثانية')
            suspicion_score += 0.2

        if login_hour < 2 or login_hour > 22:
            reasons.append(f'تسجيل دخول في وقت غير معتاد: الساعة {login_hour}:00')
            suspicion_score += 0.15

        if self.is_trained:
            try:
                scaled = self.scaler.transform(features)
                anomaly = self.isolation_forest.predict(scaled)
                if anomaly[0] == -1:
                    reasons.append('سلوك شاذ مكتشف بنموذج الذكاء الاصطناعي')
                    suspicion_score += 0.3
                rf_pred = int(self.rf_classifier.predict(scaled)[0])
                proba = float(self.rf_classifier.predict_proba(scaled)[0][1])
                if rf_pred == 1:
                    reasons.append('تصنيف الغابة العشوائية يشير إلى سلوك مشبوه')
                    suspicion_score += 0.25 * proba
            except Exception:
                pass

        if suspicion_score >= 0.5:
            result['is_suspicious'] = True
            result['confidence'] = min(suspicion_score, 1.0)
            result['reasons'] = reasons

            if suspicion_score >= 0.8:
                result['severity_level'] = 'عالية'
                result['threat_type'] = 'محاولة تصيد'
                result['description'] = 'تم رصد نمط سلوكي يشير بشكل قوي إلى هجوم تصيد إلكتروني'
            elif suspicion_score >= 0.6:
                result['severity_level'] = 'متوسطة'
                result['threat_type'] = 'نشاط مشبوه'
                result['description'] = 'تم رصد نمط سلوكي غير طبيعي يستدعي المراجعة'
            else:
                result['severity_level'] = 'منخفضة'
                result['threat_type'] = 'انحراف سلوكي'
                result['description'] = 'تم رصد انحراف طفيف عن النمط السلوكي المعتاد'

        return result

    def train_with_simulated_data(self):
        normal_data = []
        for _ in range(200):
            normal_data.append(
                [
                    np.random.uniform(3, 8),
                    np.random.randint(8, 18),
                    0,
                    np.random.uniform(120, 900),
                    np.random.uniform(0, 0.2),
                ]
            )

        suspicious_data = []
        for _ in range(50):
            suspicious_data.append(
                [
                    np.random.uniform(0.1, 1.0)
                    if np.random.random() > 0.5
                    else np.random.uniform(18, 30),
                    np.random.randint(0, 6),
                    np.random.randint(3, 10),
                    np.random.uniform(5, 30),
                    np.random.uniform(0.6, 1.0),
                ]
            )

        all_data = np.array(normal_data + suspicious_data)
        labels = [0] * 200 + [1] * 50

        self.scaler.fit(all_data)
        scaled_data = self.scaler.transform(all_data)

        self.isolation_forest.fit(scaled_data[:200])
        self.rf_classifier.fit(scaled_data, labels)

        self.is_trained = True
        self._save_model()
        return True
