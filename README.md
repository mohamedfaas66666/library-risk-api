# Library Risk Management API

مساعد ذكي لإدارة مخاطر المكتبات باستخدام الذكاء الاصطناعي.

## التشغيل المحلي

```bash
pip install -r requirements.txt
python app.py
```

## الـ Endpoints

- `POST /api/signup` - تسجيل حساب جديد
- `POST /api/login` - تسجيل الدخول
- `POST /api/chat` - إرسال سؤال للموديل
- `GET /api/health` - فحص حالة الـ API

## Deploy على Render

1. ارفع الكود على GitHub
2. اربط الـ repo بـ Render.com
3. الـ API هيشتغل تلقائياً
