"""
معالج وتنظيف بيانات مخاطر المكتبات
Data Processing & Cleaning
"""

import pandas as pd
import re
from typing import List

# قائمة كلمات التوقف العربية
ARABIC_STOP_WORDS = [
    'من', 'إلى', 'على', 'في', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
    'الذي', 'التي', 'الذين', 'اللذين', 'اللتين', 'اللواتي', 'اللائي',
    'هو', 'هي', 'هم', 'هن', 'أنا', 'نحن', 'أنت', 'أنتم', 'أنتن',
    'كان', 'كانت', 'كانوا', 'يكون', 'تكون', 'أن', 'إن', 'لأن', 'لكن',
    'أو', 'و', 'ف', 'ثم', 'أم', 'بل', 'لا', 'ما', 'لم', 'لن', 'إذا', 'إذ',
    'حتى', 'كي', 'كيف', 'أين', 'متى', 'كم', 'أي', 'ماذا', 'لماذا',
    'قد', 'لقد', 'سوف', 'س', 'ل', 'ب', 'ك', 'منذ', 'خلال', 'بين',
    'فوق', 'تحت', 'أمام', 'خلف', 'بعد', 'قبل', 'عند', 'حول', 'ضد',
    'كل', 'بعض', 'غير', 'سوى', 'مثل', 'نفس', 'ذات', 'كلا', 'كلتا',
    'هنا', 'هناك', 'الآن', 'أيضا', 'جدا', 'فقط', 'حيث', 'بينما',
    # كلمات عامية
    'ده', 'دي', 'دول', 'اللي', 'بتاع', 'بتاعة', 'بتوع', 'عشان', 'علشان',
    'كده', 'ازاي', 'إزاي', 'ليه', 'فين', 'إمتى', 'مين', 'إيه', 'أيه',
    'يعني', 'بس', 'كمان', 'برضو', 'برضه', 'خلاص', 'طيب', 'ماشي',
]


class DataProcessor:
    """معالج وتنظيف البيانات"""
    
    def __init__(self, input_path: str="risk_data.csv"):
        self.input_path = input_path
        self.df = None
        self.load_data()
    
    def load_data(self) -> pd.DataFrame:
        """تحميل البيانات"""
        self.df = pd.read_csv(self.input_path, encoding="utf-8-sig")
        print(f"تم تحميل {len(self.df)} سجل")
        return self.df
    
    def remove_duplicates(self) -> pd.DataFrame:
        """إزالة التكرارات"""
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=['مشكلة'], keep='first')
        after = len(self.df)
        print(f"تم إزالة {before - after} سجل مكرر")
        return self.df
    
    def clean_text(self, text: str) -> str:
        """تنظيف النص"""
        if pd.isna(text):
            return ""
        
        text = str(text)
        
        # إزالة الأحرف الخاصة مع الحفاظ على العربية والأرقام
        text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\s0-9a-zA-Z]', ' ', text)
        
        # إزالة المسافات المتعددة
        text = re.sub(r'\s+', ' ', text)
        
        # إزالة المسافات في البداية والنهاية
        text = text.strip()
        
        return text
    
    def normalize_arabic(self, text: str) -> str:
        """تطبيع النص العربي"""
        if not text:
            return ""
        
        # توحيد الألف
        text = re.sub(r'[إأآا]', 'ا', text)
        
        # توحيد الياء
        text = re.sub(r'[ىي]', 'ي', text)
        
        # توحيد التاء المربوطة
        text = re.sub(r'ة', 'ه', text)
        
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        
        return text
    
    def remove_stop_words(self, text: str) -> str:
        """إزالة كلمات التوقف"""
        if not text:
            return ""
        
        words = text.split()
        filtered_words = [w for w in words if w not in ARABIC_STOP_WORDS]
        return ' '.join(filtered_words)
    
    def handle_missing_values(self) -> pd.DataFrame:
        """معالجة القيم الفارغة"""
        before = len(self.df)
        
        # إزالة الصفوف التي بها قيم فارغة
        self.df = self.df.dropna()
        
        # إزالة الصفوف التي بها نصوص فارغة
        self.df = self.df[self.df['مشكلة'].str.strip() != '']
        self.df = self.df[self.df['فئة المخاطر'].str.strip() != '']
        self.df = self.df[self.df['الحلول'].str.strip() != '']
        
        after = len(self.df)
        print(f"تم إزالة {before - after} سجل فارغ")
        return self.df
    
    def process(self) -> pd.DataFrame:
        """تنفيذ جميع خطوات المعالجة"""
        print("بدء معالجة البيانات...")
        
        # 1. إزالة التكرارات
        self.remove_duplicates()
        
        # 2. معالجة القيم الفارغة
        self.handle_missing_values()
        
        # 3. تنظيف النصوص
        print("تنظيف النصوص...")
        self.df['مشكلة_نظيفة'] = self.df['مشكلة'].apply(self.clean_text)
        
        # 4. تطبيع النص العربي
        print("تطبيع النص العربي...")
        self.df['مشكلة_نظيفة'] = self.df['مشكلة_نظيفة'].apply(self.normalize_arabic)
        
        # 5. إزالة كلمات التوقف (للتدريب فقط)
        print("إزالة كلمات التوقف...")
        self.df['مشكلة_للتدريب'] = self.df['مشكلة_نظيفة'].apply(self.remove_stop_words)
        
        # إزالة الصفوف الفارغة بعد التنظيف
        self.df = self.df[self.df['مشكلة_للتدريب'].str.strip() != '']
        
        print(f"اكتملت المعالجة. عدد السجلات النهائي: {len(self.df)}")
        return self.df
    
    def save_processed(self, output_path: str="processed_risk_data.csv") -> None:
        """حفظ البيانات المعالجة"""
        self.df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"تم حفظ البيانات المعالجة في {output_path}")


if __name__ == "__main__":
    processor = DataProcessor("risk_data.csv")
    processor.process()
    processor.save_processed()
    
    # عرض عينة
    print("\nعينة من البيانات المعالجة:")
    print(processor.df[['مشكلة', 'مشكلة_للتدريب', 'فئة المخاطر']].head())
