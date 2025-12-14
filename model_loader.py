"""
محمل نموذج تصنيف مخاطر المكتبات
يستخدم للتنبؤ بفئة المخاطر والحلول
"""

import pickle
import json
import re
import os


class RiskClassifier:
    """مصنف مخاطر المكتبات"""
    
    def __init__(self, model_dir: str="."):
        self.model_dir = model_dir
        self.model = None
        self.tfidf = None
        self.category_mapping = None
        self.labels = None
        self.solutions = None
        self.model_info = None
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """تحميل النموذج والملفات المساعدة"""
        try:
            # تحميل النموذج
            with open(os.path.join(self.model_dir, "best_model.pkl"), 'rb') as f:
                self.model = pickle.load(f)
            
            # تحميل TF-IDF
            with open(os.path.join(self.model_dir, "tfidf.pkl"), 'rb') as f:
                self.tfidf = pickle.load(f)
            
            # تحميل تعيين الفئات
            with open(os.path.join(self.model_dir, "category_mapping.json"), 'r', encoding='utf-8') as f:
                self.category_mapping = json.load(f)
            
            # تحميل التصنيفات
            with open(os.path.join(self.model_dir, "labels.json"), 'r', encoding='utf-8') as f:
                self.labels = json.load(f)
            
            # تحميل الحلول
            solutions_path = os.path.join(self.model_dir, "solutions.json")
            if os.path.exists(solutions_path):
                with open(solutions_path, 'r', encoding='utf-8') as f:
                    self.solutions = json.load(f)
            
            # تحميل معلومات النموذج
            info_path = os.path.join(self.model_dir, "model_info.json")
            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    self.model_info = json.load(f)
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"خطأ في تحميل النموذج: {e}")
            self.is_loaded = False
            return False
    
    def preprocess_text(self, text: str) -> str:
        """معالجة النص قبل التنبؤ"""
        if not text:
            return ""
        
        # إزالة الأحرف الخاصة
        text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\s0-9a-zA-Z]', ' ', text)
        
        # توحيد الألف
        text = re.sub(r'[إأآا]', 'ا', text)
        
        # توحيد الياء
        text = re.sub(r'[ىي]', 'ي', text)
        
        # توحيد التاء المربوطة
        text = re.sub(r'ة', 'ه', text)
        
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        
        # إزالة المسافات المتعددة
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def predict(self, problem_text: str) -> dict:
        """التنبؤ بفئة المخاطر والحلول"""
        # التحقق من تحميل النموذج
        if not self.is_loaded:
            return {
                "success": False,
                "error": "النموذج غير محمل"
            }
        
        # التحقق من النص
        if not problem_text or not problem_text.strip():
            return {
                "success": False,
                "error": "يرجى إدخال نص المشكلة"
            }
        
        try:
            # معالجة النص
            processed_text = self.preprocess_text(problem_text)
            
            # تحويل النص إلى متجه
            text_vector = self.tfidf.transform([processed_text])
            
            # التنبؤ
            prediction = self.model.predict(text_vector)[0]
            probabilities = self.model.predict_proba(text_vector)[0]
            
            # الحصول على الفئة
            category = self.category_mapping[str(prediction)]
            confidence = float(max(probabilities) * 100)
            
            # الحصول على الحلول
            solutions = self.get_solutions(category)
            
            return {
                "success": True,
                "category": category,
                "confidence": round(confidence, 2),
                "solutions": solutions,
                "all_probabilities": {
                    self.category_mapping[str(i)]: round(float(p) * 100, 2)
                    for i, p in enumerate(probabilities)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"خطأ في التنبؤ: {str(e)}"
            }
    
    def get_solutions(self, category: str) -> list:
        """الحصول على الحلول لفئة معينة"""
        if self.solutions and category in self.solutions:
            return self.solutions[category][:5]  # أول 5 حلول
        return []
    
    def get_model_info(self) -> dict:
        """الحصول على معلومات النموذج"""
        if self.model_info:
            return self.model_info
        return {}


# للاختبار
if __name__ == "__main__":
    classifier = RiskClassifier(".")
    
    if classifier.load_model():
        print("تم تحميل النموذج بنجاح!")
        print(f"معلومات النموذج: {classifier.get_model_info()}")
        
        # اختبار بعض المشاكل
        test_problems = [
            "الكمبيوتر مش شغال",
            "فيه تسريب مية في المخزن",
            "حد سرق كتاب من المكتبة",
            "الموظفين مش متدربين كويس",
            "الطابعة عطلانة",
            "الإعارة بتاخد وقت طويل"
        ]
        
        print("\n--- اختبار التنبؤات ---")
        for problem in test_problems:
            result = classifier.predict(problem)
            if result["success"]:
                print(f"\nالمشكلة: {problem}")
                print(f"الفئة: {result['category']}")
                print(f"الثقة: {result['confidence']}%")
                print(f"الحلول: {', '.join(result['solutions'][:3])}")
            else:
                print(f"خطأ: {result['error']}")
    else:
        print("فشل تحميل النموذج!")
