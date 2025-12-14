# -*- coding: utf-8 -*-
"""
Library Risk Management API - For Render.com
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import json
import re
import os
import sqlite3
import hashlib
import secrets

app = Flask(__name__)
CORS(app)

# Model paths
MODEL_DIR = "model"


# Risk Classifier
class RiskClassifier:

    def __init__(self, model_path="model"):
        self.model = pickle.load(open(f"{model_path}/best_model.pkl", "rb"))
        self.tfidf = pickle.load(open(f"{model_path}/tfidf.pkl", "rb"))
        self.labels = json.load(open(f"{model_path}/labels.json", "r", encoding="utf-8"))
        
        self.stopwords = {'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي',
                         'أن', 'إن', 'كان', 'كانت', 'يكون', 'تكون', 'هو', 'هي', 'هم', 'هن',
                         'أنا', 'نحن', 'أنت', 'أنتم', 'ما', 'ماذا', 'كيف', 'لماذا', 'متى',
                         'أين', 'هل', 'لا', 'نعم', 'أو', 'و', 'ثم', 'لكن', 'بل', 'حتى'}
    
    def clean_text(self, text):
        if not isinstance(text, str):
            text = str(text)
        text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
        text = re.sub(r'[أإآ]', 'ا', text)
        text = re.sub(r'ة', 'ه', text)
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        tokens = [w for w in text.split() if w not in self.stopwords and len(w) > 2]
        return " ".join(tokens)
    
    def predict(self, text):
        cleaned = self.clean_text(text)
        vec = self.tfidf.transform([cleaned])
        prediction = self.model.predict(vec)[0]
        
        try:
            probs = self.model.predict_proba(vec)[0]
            confidence = float(max(probs))
        except:
            confidence = 1.0
        
        return {"prediction": prediction, "confidence": confidence}


# Initialize classifier
classifier = None
try:
    classifier = RiskClassifier(MODEL_DIR)
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"⚠️ Model error: {e}")

# Risk descriptions and solutions
RISK_INFO = {
    "أمني": {
        "description": "مخاطر تتعلق بالأمن والحماية",
        "examples": ["السرقة", "التخريب", "الوصول غير المصرح به", "الاختراق الإلكتروني"],
        "solutions": [
            "تركيب كاميرات مراقبة في جميع الأماكن",
            "توظيف حراس أمن مدربين",
            "تركيب أنظمة إنذار حديثة",
            "استخدام بطاقات دخول إلكترونية",
            "عمل نسخ احتياطية للبيانات المهمة"
        ]
    },
    "بيئي": {
        "description": "مخاطر بيئية وطبيعية",
        "examples": ["الحرائق", "الفيضانات", "تسرب المياه", "الرطوبة", "الحرارة العالية"],
        "solutions": [
            "تركيب أنظمة إطفاء حريق تلقائية",
            "صيانة دورية لأنظمة التكييف والتهوية",
            "فحص الأنابيب والسباكة بانتظام",
            "استخدام أجهزة قياس الرطوبة",
            "وضع خطة إخلاء طوارئ"
        ]
    },
    "تقني": {
        "description": "مخاطر تقنية وتكنولوجية",
        "examples": ["أعطال الأنظمة", "فقدان البيانات", "انقطاع الشبكة", "فيروسات"],
        "solutions": [
            "عمل نسخ احتياطية يومية",
            "تحديث البرامج والأنظمة باستمرار",
            "استخدام برامج حماية قوية",
            "تدريب الموظفين على الأمن السيبراني",
            "وجود خطة استعادة الكوارث"
        ]
    },
    "تشغيلي": {
        "description": "مخاطر تشغيلية يومية",
        "examples": ["تأخر الخدمات", "نقص الموارد", "أخطاء العمليات"],
        "solutions": [
            "وضع إجراءات تشغيل موحدة",
            "تدريب الموظفين بشكل مستمر",
            "مراجعة العمليات دورياً",
            "توفير موارد احتياطية"
        ]
    },
    "مالي": {
        "description": "مخاطر مالية واقتصادية",
        "examples": ["نقص التمويل", "سوء إدارة الميزانية", "الاختلاس"],
        "solutions": [
            "وضع ميزانية سنوية محكمة",
            "مراجعة مالية دورية",
            "تنويع مصادر التمويل",
            "الرقابة المالية المستمرة"
        ]
    },
    "موظفين": {
        "description": "مخاطر الموارد البشرية",
        "examples": ["نقص الكوادر", "ضعف التدريب", "دوران الموظفين"],
        "solutions": [
            "برامج تدريب مستمرة",
            "تحسين بيئة العمل",
            "نظام حوافز عادل",
            "خطط تطوير وظيفي"
        ]
    },
    "قانوني": {
        "description": "مخاطر قانونية وتنظيمية",
        "examples": ["مخالفة الأنظمة", "قضايا حقوق الملكية", "عدم الامتثال"],
        "solutions": [
            "مراجعة قانونية دورية",
            "تحديث السياسات والإجراءات",
            "استشارة قانونية متخصصة",
            "تدريب على الامتثال"
        ]
    },
    "صحي": {
        "description": "مخاطر صحية وسلامة",
        "examples": ["الأوبئة", "الإصابات", "سوء التهوية"],
        "solutions": [
            "توفير معدات إسعاف أولي",
            "تعقيم دوري للمرافق",
            "تدريب على الإسعافات الأولية",
            "فحوصات صحية دورية"
        ]
    },
    "اجتماعي": {
        "description": "مخاطر اجتماعية ومجتمعية",
        "examples": ["شكاوى المستفيدين", "سوء السمعة", "ضعف التواصل"],
        "solutions": [
            "نظام شكاوى فعال",
            "استطلاعات رضا دورية",
            "تحسين خدمة العملاء",
            "برامج توعية مجتمعية"
        ]
    },
    "عام": {
        "description": "مخاطر عامة متنوعة",
        "examples": ["مخاطر غير مصنفة"],
        "solutions": [
            "تقييم شامل للمخاطر",
            "وضع خطط طوارئ",
            "مراجعة دورية للإجراءات"
        ]
    }
}

# Database
DB_PATH = "users.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


init_db()


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# Routes
@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Library Risk API is running"})


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    if not all([data.get('name'), data.get('email'), data.get('password')]):
        return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'}), 400
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
    if cur.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'البريد مسجل مسبقاً'}), 400
    
    token = secrets.token_hex(32)
    cur.execute('INSERT INTO users (name, email, password, token) VALUES (?, ?, ?, ?)',
                (data['name'], data['email'], hash_pw(data['password']), token))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'token': token, 'user_id': uid, 'name': data['name']})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not all([data.get('email'), data.get('password')]):
        return jsonify({'success': False, 'message': 'البريد وكلمة المرور مطلوبان'}), 400
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE email = ?', (data['email'],))
    user = cur.fetchone()
    
    if not user or user['password'] != hash_pw(data['password']):
        conn.close()
        return jsonify({'success': False, 'message': 'بيانات الدخول غير صحيحة'}), 401
    
    token = secrets.token_hex(32)
    cur.execute('UPDATE users SET token = ? WHERE id = ?', (token, user['id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'token': token, 'user_id': user['id'], 'name': user['name']})


@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.json.get('message', '').strip()
    if not message:
        return jsonify({'success': False, 'message': 'الرسالة مطلوبة'}), 400
    
    if not classifier:
        return jsonify({'success': False, 'message': 'النموذج غير متاح'}), 500
    
    # Get prediction
    result = classifier.predict(message)
    category = result['prediction']
    confidence = result['confidence']
    
    # Get risk info
    info = RISK_INFO.get(category, RISK_INFO['عام'])
    
    # Build response
    response = f"🔍 **تصنيف المخاطر: {category}**\n\n"
    response += f"📋 {info['description']}\n\n"
    response += f"📊 نسبة الثقة: {confidence:.1%}\n\n"
    response += "💡 **الحلول المقترحة:**\n"
    for i, sol in enumerate(info['solutions'][:4], 1):
        response += f"{i}. {sol}\n"
    
    return jsonify({
        'success': True,
        'answer': response,
        'category': category,
        'confidence': round(confidence * 100, 1)
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': classifier is not None})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
