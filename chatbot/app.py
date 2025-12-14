# -*- coding: utf-8 -*-
"""
Chatbot Backend with Login/Signup and AI Model
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============ Risk Classifier ============
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

# Load solutions
SOLUTIONS_PATH = os.path.join(BASE_DIR, "solutions.json")
SOLUTIONS_DATA = {}
if os.path.exists(SOLUTIONS_PATH):
    with open(SOLUTIONS_PATH, 'r', encoding='utf-8') as f:
        SOLUTIONS_DATA = json.load(f)

RISK_INFO = {
    "أمنية": {"description": "مخاطر أمنية", "solutions": SOLUTIONS_DATA.get("أمنية", ["تركيب كاميرات", "توظيف حراس"])},
    "بيئية": {"description": "مخاطر بيئية", "solutions": SOLUTIONS_DATA.get("بيئية", ["تركيب تكييف", "صيانة تهوية"])},
    "تقنية": {"description": "مخاطر تقنية", "solutions": SOLUTIONS_DATA.get("تقنية", ["تحديث الأنظمة", "نسخ احتياطية"])},
    "تشغيلية": {"description": "مخاطر تشغيلية", "solutions": SOLUTIONS_DATA.get("تشغيلية", ["إجراءات موحدة", "تدريب"])},
    "إدارية": {"description": "مخاطر إدارية", "solutions": SOLUTIONS_DATA.get("إدارية", ["خطة استراتيجية", "تحسين التواصل"])},
    "مادية/معدات": {"description": "مخاطر مادية", "solutions": SOLUTIONS_DATA.get("مادية/معدات", ["صيانة دورية", "استبدال قديم"])},
    "عام": {"description": "مخاطر عامة", "solutions": ["تقييم شامل", "خطط طوارئ"]}
}

# ============ Database ============
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


def get_user_by_token(token):
    if not token: return None
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE token = ?', (token,))
    user = cur.fetchone()
    conn.close()
    return user


# ============ Routes ============
@app.route('/')
def home():
    return send_file(os.path.join(BASE_DIR, 'index.html'))


@app.route('/style.css')
def style():
    return send_file(os.path.join(BASE_DIR, 'style.css'), mimetype='text/css')


@app.route('/app.js')
def js():
    return send_file(os.path.join(BASE_DIR, 'app.js'), mimetype='application/javascript')


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
    conn.close()
    return jsonify({'success': True, 'token': token, 'name': data['name']})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE email = ?', (data.get('email'),))
    user = cur.fetchone()
    
    if not user or user['password'] != hash_pw(data.get('password', '')):
        conn.close()
        return jsonify({'success': False, 'message': 'بيانات غير صحيحة'}), 401
    
    token = secrets.token_hex(32)
    cur.execute('UPDATE users SET token = ? WHERE id = ?', (token, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'token': token, 'name': user['name']})


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
    
    info = RISK_INFO.get(category, RISK_INFO['عام'])
    solutions = info['solutions'][:5]
    
    response = f"🔍 التصنيف: {category}\n📋 {info['description']}\n📊 الثقة: {confidence:.1%}\n\n💡 الحلول:\n"
    for i, sol in enumerate(solutions, 1):
        response += f"{i}. {sol}\n"
    
    return jsonify({'success': True, 'answer': response, 'category': category})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
