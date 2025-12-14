
import pickle
import json
import re


class RiskClassifier:

    def __init__(self, model_path="model_improved"):
        self.model = pickle.load(open(f"{model_path}/best_model.pkl", "rb"))
        self.tfidf = pickle.load(open(f"{model_path}/tfidf.pkl", "rb"))
        self.labels = json.load(open(f"{model_path}/labels.json", "r", encoding="utf-8"))
        self.model_info = json.load(open(f"{model_path}/model_info.json", "r", encoding="utf-8"))
        
        self.stopwords = {'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي',
                         'أن', 'إن', 'كان', 'كانت', 'يكون', 'تكون', 'هو', 'هي', 'هم', 'هن',
                         'أنا', 'نحن', 'أنت', 'أنتم', 'ما', 'ماذا', 'كيف', 'لماذا', 'متى',
                         'أين', 'هل', 'لا', 'نعم', 'أو', 'و', 'ثم', 'لكن', 'بل', 'حتى',
                         'إذا', 'لو', 'قد', 'قبل', 'بعد', 'فوق', 'تحت', 'بين', 'عند', 'منذ',
                         'خلال', 'حول', 'ضد', 'نحو', 'كل', 'بعض', 'غير', 'سوى', 'فقط'}
    
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
            top_3 = sorted(zip(self.model.classes_, probs), key=lambda x: x[1], reverse=True)[:3]
        except:
            confidence = 1.0
            top_3 = [(prediction, 1.0)]
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "top_3": top_3
        }
    
    def predict_batch(self, texts):
        return [self.predict(t) for t in texts]



if __name__ == "__main__":
    classifier = RiskClassifier("model_improved")
    
    
    result = classifier.predict("تسرب مياه في المبنى الرئيسي")
    print(f"التصنيف: {result['prediction']}")
    print(f"الثقة: {result['confidence']:.1%}")
