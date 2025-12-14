# -*- coding: utf-8 -*-
"""
Library Risk Management API - For PythonAnywhere
"""

from flask import Flask, request, jsonify, send_file
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

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Risk Classifier
class RiskClassifier:

    def __init__(self):
        self.model = pickle.load(open(os.path.join(BASE_DIR, "best_model.pkl"), "rb"))
        self.tfidf = pickle.load(open(os.path.join(BASE_DIR, "tfidf.pkl"), "rb"))
        self.labels = json.load(open(os.path.join(BASE_DIR, "labels.json"), "r", encoding="utf-8"))
        
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
model_error = None
try:
    classifier = RiskClassifier()
    print("✅ Model loaded successfully")
except Exception as e:
    model_error = str(e)
    print(f"⚠️ Model error: {e}")
    import traceback
    traceback.print_exc()

# Load solutions from JSON file (trained on 50,000 problems)
SOLUTIONS_PATH = os.path.join(BASE_DIR, "solutions.json")
if os.path.exists(SOLUTIONS_PATH):
    with open(SOLUTIONS_PATH, 'r', encoding='utf-8') as f:
        SOLUTIONS_DATA = json.load(f)
else:
    SOLUTIONS_DATA = {}

# Risk descriptions and solutions (6 categories - 99.95% accuracy model)
RISK_INFO = {
    "أمنية": {
        "description": "مخاطر تتعلق بالأمن والحماية والسرقة والتخريب",
        "solutions": SOLUTIONS_DATA.get("أمنية", ["تركيب كاميرات مراقبة", "توظيف حراس أمن", "تركيب بوابات إلكترونية", "وضع شرائح أمان على الكتب"])
    },
    "بيئية": {
        "description": "مخاطر بيئية وطبيعية مثل الرطوبة والحرارة والحشرات",
        "solutions": SOLUTIONS_DATA.get("بيئية", ["تركيب نظام تكييف مركزي", "صيانة دورية لنظام التهوية", "عزل النوافذ والأسقف", "رش مبيدات حشرية آمنة"])
    },
    "تقنية": {
        "description": "مخاطر تقنية وتكنولوجية مثل أعطال الأنظمة والشبكات",
        "solutions": SOLUTIONS_DATA.get("تقنية", ["تحديث الأنظمة بانتظام", "عمل نسخ احتياطية يومية", "تركيب برامج حماية", "التعاقد مع دعم فني"])
    },
    "تشغيلية": {
        "description": "مخاطر تشغيلية يومية مثل تأخر الخدمات وأخطاء العمليات",
        "solutions": SOLUTIONS_DATA.get("تشغيلية", ["وضع إجراءات تشغيلية موحدة", "تدريب الموظفين على الإجراءات", "أتمتة العمليات الروتينية", "متابعة دورية للعمليات"])
    },
    "إدارية": {
        "description": "مخاطر إدارية مثل نقص الموظفين وضعف التواصل",
        "solutions": SOLUTIONS_DATA.get("إدارية", ["وضع خطة استراتيجية", "تحسين التواصل الداخلي", "توفير ميزانية كافية", "تدريب وتطوير الموظفين"])
    },
    "مادية/معدات": {
        "description": "مخاطر مادية ومعدات مثل أعطال الأجهزة والأثاث",
        "solutions": SOLUTIONS_DATA.get("مادية/معدات", ["صيانة دورية للمعدات", "استبدال المعدات القديمة", "توفير قطع غيار احتياطية", "التعاقد مع شركة صيانة"])
    },
    "عام": {
        "description": "مخاطر عامة متنوعة",
        "solutions": ["تقييم شامل للمخاطر", "خطط طوارئ", "مراجعة دورية للإجراءات"]
    }
}

# Database
DB_PATH = os.path.join(BASE_DIR, "users.db")


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
    return send_file(os.path.join(BASE_DIR, 'index.html'))


@app.route('/style.css')
def style():
    return send_file(os.path.join(BASE_DIR, 'style.css'), mimetype='text/css')


@app.route('/app.js')
def js():
    return send_file(os.path.join(BASE_DIR, 'app.js'), mimetype='application/javascript')


@app.route('/images/<path:filename>')
def images(filename):
    return send_file(os.path.join(BASE_DIR, filename))


@app.route('/<path:filename>')
def static_files(filename):
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return "Not found", 404


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
        return jsonify({'success': False, 'message': f'النموذج غير متاح: {model_error}'}), 500
    
    result = classifier.predict(message)
    category = result['prediction']
    confidence = result['confidence']
    
    # Get info from RISK_INFO, try exact match first, then partial match
    info = RISK_INFO.get(category)
    if not info:
        # Try to find partial match
        for key in RISK_INFO:
            if key in category or category in key:
                info = RISK_INFO[key]
                break
        if not info:
            info = RISK_INFO['عام']
    
    response = f"🔍 تصنيف المخاطر: {category}\n\n"
    response += f"📋 {info['description']}\n\n"
    response += f"📊 نسبة الثقة: {confidence:.1%}\n\n"
    response += "💡 الحلول المقترحة:\n"
    solutions = info['solutions'][:5] if len(info['solutions']) > 5 else info['solutions']
    for i, sol in enumerate(solutions, 1):
        response += f"{i}. {sol}\n"
    
    return jsonify({
        'success': True,
        'answer': response,
        'category': category,
        'confidence': round(confidence * 100, 1)
    })


@app.route('/api/health', methods=['GET'])
def health():
    model_info_path = os.path.join(BASE_DIR, "model_info.json")
    info = {}
    if os.path.exists(model_info_path):
        with open(model_info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
    return jsonify({
        'status': 'ok',
        'model': classifier is not None,
        'accuracy': info.get('accuracy', 0),
        'num_samples': info.get('num_samples', 0),
        'categories': info.get('categories', [])
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
