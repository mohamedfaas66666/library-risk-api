"""
تطبيق Flask لنظام إدارة مخاطر المكتبات
مع قاعدة بيانات لكل مستخدم
"""

from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
import sqlite3
import os
import uuid
from datetime import datetime
from model_loader import RiskClassifier

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# تحميل النموذج
classifier = RiskClassifier(".")
model_loaded = classifier.load_model()

# مسار قاعدة البيانات
DB_PATH = "library_risks.db"


def init_db():
    """إنشاء قاعدة البيانات والجداول"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول المشاكل
    c.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            category TEXT NOT NULL,
            confidence REAL NOT NULL,
            solutions TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def get_or_create_user():
    """الحصول على معرف المستخدم أو إنشاء واحد جديد"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        
        # إضافة المستخدم لقاعدة البيانات
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (session['user_id'],))
        conn.commit()
        conn.close()
    
    return session['user_id']


def save_problem(user_id, problem_text, category, confidence, solutions):
    """حفظ المشكلة في قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO problems (user_id, problem_text, category, confidence, solutions)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, problem_text, category, confidence, ','.join(solutions)))
    conn.commit()
    conn.close()


def get_user_problems(user_id):
    """الحصول على مشاكل المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT problem_text, category, confidence, solutions, created_at
        FROM problems
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    problems = c.fetchall()
    conn.close()
    
    return [{
        'problem': p[0],
        'category': p[1],
        'confidence': p[2],
        'solutions': p[3].split(','),
        'created_at': p[4]
    } for p in problems]


# إنشاء قاعدة البيانات عند بدء التطبيق
init_db()


@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/predict', methods=['POST'])
def predict():
    """التنبؤ بفئة المخاطر"""
    if not model_loaded:
        return jsonify({
            'success': False,
            'error': 'النموذج غير متاح حالياً'
        }), 500
    
    data = request.get_json()
    problem_text = data.get('problem', '').strip()
    
    if not problem_text:
        return jsonify({
            'success': False,
            'error': 'يرجى إدخال نص المشكلة'
        }), 400
    
    # التنبؤ
    result = classifier.predict(problem_text)
    
    if result['success']:
        # حفظ المشكلة للمستخدم
        user_id = get_or_create_user()
        save_problem(
            user_id,
            problem_text,
            result['category'],
            result['confidence'],
            result['solutions']
        )
    
    return jsonify(result)


@app.route('/history', methods=['GET'])
def history():
    """الحصول على سجل المشاكل للمستخدم"""
    user_id = get_or_create_user()
    problems = get_user_problems(user_id)
    return jsonify({
        'success': True,
        'problems': problems
    })


@app.route('/clear-history', methods=['POST'])
def clear_history():
    """مسح سجل المشاكل للمستخدم"""
    user_id = get_or_create_user()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM problems WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'تم مسح السجل'})


@app.route('/model-info', methods=['GET'])
def model_info():
    """معلومات النموذج"""
    if model_loaded:
        return jsonify({
            'success': True,
            'info': classifier.get_model_info()
        })
    return jsonify({
        'success': False,
        'error': 'النموذج غير محمل'
    }), 500


# قالب HTML
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مساعد إدارة مخاطر المكتبات</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Cairo', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #fff;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: #a0a0a0;
            font-size: 1.1rem;
        }
        
        .input-section {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        
        .input-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        textarea {
            flex: 1;
            min-width: 300px;
            padding: 15px;
            border: 2px solid rgba(233, 69, 96, 0.3);
            border-radius: 15px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-family: 'Cairo', sans-serif;
            font-size: 1rem;
            resize: vertical;
            min-height: 100px;
        }
        
        textarea:focus {
            outline: none;
            border-color: #e94560;
        }
        
        textarea::placeholder {
            color: #888;
        }
        
        button {
            padding: 15px 40px;
            background: linear-gradient(135deg, #e94560, #ff6b6b);
            border: none;
            border-radius: 15px;
            color: #fff;
            font-family: 'Cairo', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(233, 69, 96, 0.4);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .result-section {
            display: none;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .category-badge {
            display: inline-block;
            padding: 10px 25px;
            border-radius: 30px;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
        }
        
        .category-بيئية { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .category-مادية\\/معدات { background: linear-gradient(135deg, #f093fb, #f5576c); }
        .category-تشغيلية { background: linear-gradient(135deg, #4facfe, #00f2fe); }
        .category-تقنية { background: linear-gradient(135deg, #667eea, #764ba2); }
        .category-أمنية { background: linear-gradient(135deg, #ff416c, #ff4b2b); }
        .category-إدارية { background: linear-gradient(135deg, #f7971e, #ffd200); color: #333; }
        
        .confidence {
            font-size: 1rem;
            color: #a0a0a0;
            margin-bottom: 20px;
        }
        
        .solutions-title {
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #e94560;
        }
        
        .solutions-list {
            list-style: none;
        }
        
        .solutions-list li {
            padding: 12px 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            margin-bottom: 10px;
            border-right: 4px solid #e94560;
        }
        
        .history-section {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .history-title {
            font-size: 1.5rem;
            color: #e94560;
        }
        
        .clear-btn {
            padding: 8px 20px;
            font-size: 0.9rem;
            background: rgba(233, 69, 96, 0.2);
        }
        
        .history-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .history-item {
            background: rgba(255,255,255,0.03);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .history-problem {
            font-size: 1.1rem;
            margin-bottom: 10px;
        }
        
        .history-meta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            font-size: 0.9rem;
            color: #888;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(233, 69, 96, 0.3);
            border-top-color: #e94560;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @media (max-width: 600px) {
            h1 { font-size: 1.8rem; }
            .input-group { flex-direction: column; }
            textarea { min-width: 100%; }
            button { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 مساعد إدارة مخاطر المكتبات</h1>
            <p class="subtitle">نظام ذكي لتصنيف المشاكل واقتراح الحلول</p>
        </header>
        
        <div class="input-section">
            <div class="input-group">
                <textarea id="problemInput" placeholder="اكتب المشكلة هنا... مثال: الكمبيوتر مش شغال، فيه تسريب مية في المخزن"></textarea>
                <button id="analyzeBtn" onclick="analyzeProblem()">تحليل المشكلة</button>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>جاري التحليل...</p>
        </div>
        
        <div class="result-section" id="resultSection">
            <span class="category-badge" id="categoryBadge"></span>
            <p class="confidence" id="confidence"></p>
            <h3 class="solutions-title">💡 الحلول المقترحة:</h3>
            <ul class="solutions-list" id="solutionsList"></ul>
        </div>
        
        <div class="history-section">
            <div class="history-header">
                <h2 class="history-title">📋 سجل المشاكل</h2>
                <button class="clear-btn" onclick="clearHistory()">مسح السجل</button>
            </div>
            <div class="history-list" id="historyList">
                <div class="empty-state">لا توجد مشاكل مسجلة بعد</div>
            </div>
        </div>
    </div>
    
    <script>
        // تحميل السجل عند فتح الصفحة
        document.addEventListener('DOMContentLoaded', loadHistory);
        
        async function analyzeProblem() {
            const input = document.getElementById('problemInput');
            const problem = input.value.trim();
            
            if (!problem) {
                alert('يرجى إدخال نص المشكلة');
                return;
            }
            
            const btn = document.getElementById('analyzeBtn');
            const loading = document.getElementById('loading');
            const resultSection = document.getElementById('resultSection');
            
            btn.disabled = true;
            loading.style.display = 'block';
            resultSection.style.display = 'none';
            
            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ problem: problem })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayResult(data);
                    loadHistory();
                    input.value = '';
                } else {
                    alert(data.error || 'حدث خطأ');
                }
            } catch (error) {
                alert('حدث خطأ في الاتصال');
            } finally {
                btn.disabled = false;
                loading.style.display = 'none';
            }
        }
        
        function displayResult(data) {
            const resultSection = document.getElementById('resultSection');
            const categoryBadge = document.getElementById('categoryBadge');
            const confidence = document.getElementById('confidence');
            const solutionsList = document.getElementById('solutionsList');
            
            categoryBadge.textContent = data.category;
            categoryBadge.className = 'category-badge category-' + data.category;
            
            confidence.textContent = `نسبة الثقة: ${data.confidence}%`;
            
            solutionsList.innerHTML = data.solutions
                .map((s, i) => `<li>${i + 1}. ${s}</li>`)
                .join('');
            
            resultSection.style.display = 'block';
        }
        
        async function loadHistory() {
            try {
                const response = await fetch('/history');
                const data = await response.json();
                
                const historyList = document.getElementById('historyList');
                
                if (data.success && data.problems.length > 0) {
                    historyList.innerHTML = data.problems.map(p => `
                        <div class="history-item">
                            <p class="history-problem">${p.problem}</p>
                            <div class="history-meta">
                                <span class="category-badge category-${p.category}" style="padding: 5px 15px; font-size: 0.9rem;">${p.category}</span>
                                <span>الثقة: ${p.confidence}%</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    historyList.innerHTML = '<div class="empty-state">لا توجد مشاكل مسجلة بعد</div>';
                }
            } catch (error) {
                console.error('Error loading history:', error);
            }
        }
        
        async function clearHistory() {
            if (!confirm('هل أنت متأكد من مسح السجل؟')) return;
            
            try {
                await fetch('/clear-history', { method: 'POST' });
                loadHistory();
            } catch (error) {
                alert('حدث خطأ');
            }
        }
        
        // إرسال بالضغط على Enter
        document.getElementById('problemInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                analyzeProblem();
            }
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 50)
    print("مساعد إدارة مخاطر المكتبات")
    print("=" * 50)
    if model_loaded:
        print("✅ تم تحميل النموذج بنجاح")
        print(f"📊 دقة النموذج: {classifier.get_model_info().get('accuracy', 0) * 100:.2f}%")
    else:
        print("❌ فشل تحميل النموذج")
    print("=" * 50)
    print("🌐 التطبيق يعمل على: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
