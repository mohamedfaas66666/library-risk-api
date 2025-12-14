# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import json
import re

app = Flask(__name__)
CORS(app)

# Load model
model = pickle.load(open("best_model.pkl", "rb"))
tfidf = pickle.load(open("tfidf.pkl", "rb"))
labels = json.load(open("labels.json", "r", encoding="utf-8"))
solutions = json.load(open("solutions.json", "r", encoding="utf-8"))

STOPWORDS = {'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي',
             'أن', 'إن', 'كان', 'كانت', 'يكون', 'تكون', 'هو', 'هي', 'هم', 'هن',
             'أنا', 'نحن', 'أنت', 'أنتم', 'ما', 'ماذا', 'كيف', 'لماذا', 'متى',
             'أين', 'هل', 'لا', 'نعم', 'أو', 'و', 'ثم', 'لكن', 'بل', 'حتى'}


def clean_text(text):
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', str(text))
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = [w for w in text.split() if w not in STOPWORDS and len(w) > 2]
    return " ".join(tokens)


def predict(text):
    cleaned = clean_text(text)
    vec = tfidf.transform([cleaned])
    prediction = model.predict(vec)[0]
    try:
        probs = model.predict_proba(vec)[0]
        confidence = float(max(probs))
    except:
        confidence = 0.7
    return prediction, confidence


@app.route('/')
def home():
    return jsonify({'status': 'ok', 'message': 'Library Risk Management API'})


@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.json
    if not data or not data.get('text'):
        return jsonify({'success': False, 'message': 'النص مطلوب'}), 400
    
    category, confidence = predict(data['text'])
    category_solutions = solutions.get(category, [])
    
    return jsonify({
        'success': True,
        'category': category,
        'confidence': round(confidence * 100, 1),
        'solutions': category_solutions[:5]
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify({'success': True, 'categories': labels})


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run()
