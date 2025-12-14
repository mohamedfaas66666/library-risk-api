"""
تدريب نموذج تصنيف مخاطر المكتبات
Random Forest + TF-IDF
"""

import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder


class RiskClassifierTrainer:
    """مدرب نموذج تصنيف المخاطر"""
    
    def __init__(self, data_path: str="processed_risk_data.csv"):
        self.data_path = data_path
        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.tfidf = None
        self.model = None
        self.label_encoder = None
        self.accuracy = 0.0
        
    def load_data(self) -> pd.DataFrame:
        """تحميل البيانات المعالجة"""
        self.df = pd.read_csv(self.data_path, encoding="utf-8-sig")
        print(f"تم تحميل {len(self.df)} سجل للتدريب")
        return self.df
    
    def prepare_features(self):
        """تحضير الميزات باستخدام TF-IDF"""
        print("تحضير الميزات باستخدام TF-IDF...")
        
        # إنشاء TF-IDF Vectorizer
        self.tfidf = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # unigrams و bigrams
            min_df=2,
            max_df=0.95
        )
        
        # تحويل النصوص إلى متجهات
        X = self.tfidf.fit_transform(self.df['مشكلة_للتدريب'])
        
        # ترميز التصنيفات
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(self.df['فئة المخاطر'])
        
        print(f"عدد الميزات: {X.shape[1]}")
        print(f"الفئات: {list(self.label_encoder.classes_)}")
        
        return X, y
    
    def split_data(self, X, y, test_size: float=0.2):
        """تقسيم البيانات للتدريب والاختبار"""
        print(f"تقسيم البيانات: {int((1-test_size)*100)}% تدريب، {int(test_size*100)}% اختبار")
        
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"حجم بيانات التدريب: {self.X_train.shape[0]}")
        print(f"حجم بيانات الاختبار: {self.X_test.shape[0]}")
    
    def train_random_forest(self):
        """تدريب نموذج Random Forest"""
        print("\nتدريب نموذج Random Forest...")
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        self.model.fit(self.X_train, self.y_train)
        print("اكتمل التدريب!")
    
    def evaluate(self):
        """تقييم النموذج"""
        print("\nتقييم النموذج...")
        
        # التنبؤ على بيانات الاختبار
        y_pred = self.model.predict(self.X_test)
        
        # حساب الدقة
        self.accuracy = accuracy_score(self.y_test, y_pred)
        print(f"\nالدقة الكلية: {self.accuracy * 100:.2f}%")
        
        # تقرير التصنيف
        print("\nتقرير التصنيف:")
        target_names = list(self.label_encoder.classes_)
        print(classification_report(self.y_test, y_pred, target_names=target_names))
        
        # مصفوفة الارتباك
        print("\nمصفوفة الارتباك:")
        cm = confusion_matrix(self.y_test, y_pred)
        print(pd.DataFrame(cm, index=target_names, columns=target_names))
        
        return self.accuracy
    
    def save_model(self, output_dir: str="."):
        """حفظ النموذج والملفات المساعدة"""
        print(f"\nحفظ النموذج في {output_dir}...")
        
        # حفظ النموذج
        with open(f"{output_dir}/best_model.pkl", 'wb') as f:
            pickle.dump(self.model, f)
        print("تم حفظ best_model.pkl")
        
        # حفظ TF-IDF
        with open(f"{output_dir}/tfidf.pkl", 'wb') as f:
            pickle.dump(self.tfidf, f)
        print("تم حفظ tfidf.pkl")
        
        # حفظ تعيين الفئات
        category_mapping = {
            int(i): label for i, label in enumerate(self.label_encoder.classes_)
        }
        with open(f"{output_dir}/category_mapping.json", 'w', encoding='utf-8') as f:
            json.dump(category_mapping, f, ensure_ascii=False, indent=2)
        print("تم حفظ category_mapping.json")
        
        # حفظ التصنيفات
        labels = list(self.label_encoder.classes_)
        with open(f"{output_dir}/labels.json", 'w', encoding='utf-8') as f:
            json.dump(labels, f, ensure_ascii=False, indent=2)
        print("تم حفظ labels.json")
        
        # حفظ معلومات النموذج
        model_info = {
            "training_date": datetime.now().isoformat(),
            "accuracy": float(self.accuracy),
            "num_samples": len(self.df),
            "num_features": self.tfidf.max_features,
            "model_type": "RandomForestClassifier",
            "categories": labels
        }
        with open(f"{output_dir}/model_info.json", 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)
        print("تم حفظ model_info.json")
        
        # حفظ الحلول لكل فئة
        solutions_by_category = {}
        for category in labels:
            cat_solutions = self.df[self.df['فئة المخاطر'] == category]['الحلول'].unique()
            # تجميع كل الحلول الفريدة
            all_solutions = set()
            for sol_str in cat_solutions:
                solutions = [s.strip() for s in str(sol_str).split('،')]
                all_solutions.update(solutions)
            solutions_by_category[category] = list(all_solutions)
        
        with open(f"{output_dir}/solutions.json", 'w', encoding='utf-8') as f:
            json.dump(solutions_by_category, f, ensure_ascii=False, indent=2)
        print("تم حفظ solutions.json")
    
    def train(self):
        """تنفيذ عملية التدريب الكاملة"""
        # 1. تحميل البيانات
        self.load_data()
        
        # 2. تحضير الميزات
        X, y = self.prepare_features()
        
        # 3. تقسيم البيانات
        self.split_data(X, y)
        
        # 4. تدريب النموذج
        self.train_random_forest()
        
        # 5. تقييم النموذج
        accuracy = self.evaluate()
        
        # 6. حفظ النموذج
        self.save_model()
        
        return accuracy


if __name__ == "__main__":
    trainer = RiskClassifierTrainer("processed_risk_data.csv")
    accuracy = trainer.train()
    
    if accuracy >= 0.70:
        print(f"\n✅ النموذج حقق الدقة المطلوبة: {accuracy*100:.2f}%")
    else:
        print(f"\n⚠️ النموذج لم يحقق الدقة المطلوبة (70%): {accuracy*100:.2f}%")
