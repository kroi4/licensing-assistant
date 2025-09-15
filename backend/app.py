# backend/app.py
import os
import json
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_helper import generate_ai_report

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
# Configure CORS to allow all origins (for development)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# --- כללי: מאפייני קלט נתמכים ---
# features אפשריים: "gas", "delivery", "alcohol", "hood", "meat"
# area (float > 0), seats (int >= 0)

# Global variable to hold restaurant rules
RESTAURANT_RULES: List[Dict[str, Any]] = []

def load_restaurant_rules():
    """Load restaurant rules from JSON file"""
    global RESTAURANT_RULES
    
    # Path to rules file
    rules_path = os.path.join(os.path.dirname(__file__), "rules", "restaurant_rules.json")
    
    try:
        if os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8') as f:
                RESTAURANT_RULES = json.load(f)
            print(f"Loaded {len(RESTAURANT_RULES)} rules from {rules_path}")
        else:
            print(f"Rules file not found at {rules_path}, using fallback rules")
            RESTAURANT_RULES = get_fallback_rules()
    except Exception as e:
        print(f"Error loading rules from {rules_path}: {e}")
        print("Using fallback rules")
        RESTAURANT_RULES = get_fallback_rules()

def get_fallback_rules():
    """Fallback rules in case JSON file is not available"""
    return [
    # משרד הבריאות – בסיס
    {
        "id": "health-baseline",
        "category": "משרד הבריאות",
        "title": "עמידה בתנאי תברואה לבתי אוכל + מי שתייה ושפכים",
        "status": "חובה",
        "note": "תקנות בתי אוכל, איכות מי שתייה, מניעת עישון ושילוט.",
        "section_ref": "בריאות – תנאים רוחביים",
        "if": {}
    },
    {
        "id": "health-smoking-signage",
        "category": "משרד הבריאות",
        "title": "שילוט איסור עישון והפרדה אזורי עישון (אם יש)",
        "status": "חובה",
        "note": "חוק למניעת העישון ותקנות שילוט.",
        "if": {}
    },

    # משרד הבריאות – שליחת מזון
    {
        "id": "delivery-rules",
        "category": "משרד הבריאות — שליחת מזון",
        "title": "דרישות לשליחת מזון",
        "status": "חובה",
        "note": "אזור ייעודי, קירור/הקפאה, בקרה ותיעוד טמפרטורות, ציוד אריזה, והובלה עד 3 שעות.",
        "if": {"features_all": ["delivery"]}
    },

    # משטרה – נדרש אם אלכוהול
    {
        "id": "police-alcohol",
        "category": "משטרת ישראל",
        "title": "דרישות משטרה עקב הגשת/מכירת אלכוהול",
        "status": "חובה",
        "note": "טמ״ס, תאורה חיצונית, שילוט איסור מכירה <18, החזקת הקלטות 14 יום וכו’.",
        "if": {"features_all": ["alcohol"]}
    },
    # משטרה – נדרש אם מעל 200 מקומות
    {
        "id": "police-capacity",
        "category": "משטרת ישראל",
        "title": "דרישות משטרה עקב תפוסה > 200",
        "status": "חובה",
        "note": "טמ״ס/שילוט/תאורה לפי פרק 3.",
        "if": {"seats_min": 201}
    },

    # כבאות – מסלול תצהיר (קטנים)
    {
        "id": "fire-affidavit",
        "category": "כבאות והצלה (תצהיר)",
        "title": "מסלול תצהיר – עד 50 איש ועד 150 מ״ר",
        "status": "חובה",
        "note": "עמידה בדרישות פרק 5 – שילוט יציאות, תאורת חירום, מטפים וכו’.",
        "if": {"seats_max": 50, "area_max": 150}
    },
    # כבאות – מסלול מלא (גדולים) – שני טריגרים נפרדים כדי לכסות OR
    {
        "id": "fire-full-area",
        "category": "כבאות והצלה",
        "title": "מסלול מלא – שטח מעל 150 מ״ר",
        "status": "חובה",
        "note": "דרכי מוצא, עמדות כיבוי, תאורת חירום, ייתכן מתזים/גילוי עשן לפי ספים.",
        "if": {"area_min": 151}
    },
    {
        "id": "fire-full-seats",
        "category": "כבאות והצלה",
        "title": "מסלול מלא – תפוסה מעל 50",
        "status": "חובה",
        "note": "דרכי מוצא, עמדות כיבוי, תאורת חירום, ייתכן מתזים/גילוי עשן לפי ספים.",
        "if": {"seats_min": 51}
    },

    # גז
    {
        "id": "gas-cert",
        "category": "גז (גפ\"מ)",
        "title": "אישור מתקין גפ\"מ ועמידה בת״י 158",
        "status": "חובה",
        "note": "בדיקות תקינות, ניתוקי חירום, תחזוקה שוטפת.",
        "if": {"features_all": ["gas"]}
    },
    {
        "id": "hood-suppression",
        "category": "כבאות – מנדפים",
        "title": "מערכת כיבוי למנדפים במטבח מקצועי",
        "status": "חובה",
        "note": "מערכת כימיקלים רטובים/לפי ת״י 5356-2 + ניתוק אנרגיה.",
        "if": {"features_any": ["gas", "hood", "meat"]}
    },
    {
        "id": "meat-handling",
        "category": "משרד הבריאות",
        "title": "דרישות טיפול בבשר",
        "status": "חובה",
        "note": "הפרדת בשר וחלב, אחסון נפרד, בקרת טמפרטורות.",
        "if": {"features_any": ["meat"]}
    }
]

# Load rules on startup
load_restaurant_rules()

def translate_features(features: List[str]) -> List[str]:
    """תרגום מאפיינים מאנגלית לעברית"""
    feature_translations = {
        "gas": "שימוש בגז",
        "delivery": "שירות משלוחים", 
        "alcohol": "הגשת אלכוהול",
        "hood": "מנדף מטבח מקצועי",
        "meat": "הגשת בשר"
    }
    return [feature_translations.get(feature, feature) for feature in features]

def rule_matches(cond: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    area = payload.get("area")
    seats = payload.get("seats")
    features = set(payload.get("features") or [])
    if "area_min" in cond and (area is None or area < cond["area_min"]): return False
    if "area_max" in cond and (area is None or area > cond["area_max"]): return False
    if "seats_min" in cond and (seats is None or seats < cond["seats_min"]): return False
    if "seats_max" in cond and (seats is None or seats > cond["seats_max"]): return False
    if "features_any" in cond and features.isdisjoint(set(cond["features_any"])): return False
    if "features_all" in cond and not set(cond["features_all"]).issubset(features): return False
    return True

def evaluate_restaurant(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    מקבל נתוני מסעדה ומחזיר את הדרישות הרגולטוריות המתאימות
    """
    
    # בדיקת תקינות קלט בסיסית
    if not all(k in payload for k in ['area', 'seats', 'features']):
        return {"error": "חסרים שדות חובה (area, seats, features)"}
    
    area = payload['area']
    seats = payload['seats'] 
    features = set(payload['features'])

    # 1. קביעת מסלול כבאות
    is_small = area <= 150 and seats <= 50
    fire_track = "תצהיר (פרק 5)" if is_small else "מסלול מלא (פרק 6)"
    
    # 2. קביעת דרישות משטרה
    has_alcohol = "alcohol" in features
    high_capacity = seats > 200
    police_required = has_alcohol or high_capacity
    police_note = "פטור מדרישות משטרה (≤200 מקומות וללא אלכוהול)" if not police_required else "חלים תנאי משטרה"

    # 3. התאמת כללים לפי המאפיינים
    matched_rules = []
    for rule in RESTAURANT_RULES:
        if rule_matches(rule.get("if", {}), payload):
            matched_rules.append({
                "id": rule["id"],
                "category": rule["category"], 
                "title": rule["title"],
                "status": rule["status"],
                "note": rule.get("note", ""),
                "section_ref": rule.get("section_ref", "")
            })

    summary = {
        "type": "restaurant",
        "area": area,
        "seats": seats,
        "features": translate_features(list(features)),
        "police": police_note,
        "fire_track": fire_track
    }
    
    result = {
        "summary": summary,
        "checklist": matched_rules
    }

    # 4. הפקת דו"ח AI - רק אם יש חיבור אמיתי לChatGPT
    has_real_ai = False
    
    try:
        ai_report = generate_ai_report(payload, matched_rules)
        if ai_report is not None:
            # יש דוח AI אמיתי מChatGPT
            has_real_ai = True
            result['ai_report'] = ai_report
            print("✅ דוח AI נוצר בהצלחה מChatGPT")
        else:
            print("❌ אין חיבור לChatGPT - לא יוצג דוח AI")
            
    except Exception as e:
        print(f"❌ שגיאה בחיבור לChatGPT: {str(e)}")
    
    # הוסף מידע על מצב ה-AI האמיתי
    result['has_real_ai'] = has_real_ai
    if not has_real_ai:
        result['ai_status'] = "אין חיבור לChatGPT - דוח AI לא זמין"
        # אל תוסיף ai_report בכלל כשאין AI אמיתי!

    return result

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@app.post("/api/assess")
def assess():
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate required fields exist
        if not all(k in data for k in ['area', 'seats', 'features']):
            return jsonify({"error": "חסרים שדות חובה: area, seats, features"}), 400
        
        # Validate area and seats are valid numbers
        try:
            area = float(data['area'])
            seats = int(data['seats'])
            if area <= 0 or seats < 0:
                return jsonify({"error": "שטח חייב להיות גדול מ-0 ומספר מקומות ישיבה לא יכול להיות שלילי"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "שטח ומספר מקומות ישיבה חייבים להיות מספרים תקינים"}), 400
        
        # Validate features
        features = data.get('features', [])
        if not isinstance(features, list):
            return jsonify({"error": "מאפיינים חייבים להיות רשימה"}), 400
        
        if not features or len(features) == 0:
            return jsonify({"error": "חובה לבחור לפחות מאפיין אחד"}), 400
        
        # Validate that features are from the allowed list
        allowed_features = ['gas', 'delivery', 'alcohol', 'hood', 'meat']
        invalid_features = [f for f in features if f not in allowed_features]
        if invalid_features:
            return jsonify({"error": f"מאפיינים לא תקינים: {', '.join(invalid_features)}. מאפיינים מותרים: {', '.join(allowed_features)}"}), 400
        
        # Log the received data for debugging
        print(f"Received data: {data}")
        
        result = evaluate_restaurant(data)
        
        # Log the result for debugging
        print(f"Evaluation result: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in assess endpoint: {str(e)}")
        return jsonify({"error": f"שגיאה בעיבוד הבקשה: {str(e)}"}), 500

@app.post("/api/reload-rules")
def reload_rules():
    """Reload rules from JSON file (development endpoint)"""
    try:
        load_restaurant_rules()
        return jsonify({
            "ok": True, 
            "message": "Rules reloaded successfully",
            "count": len(RESTAURANT_RULES)
        })
    except Exception as e:
        print(f"Error reloading rules: {str(e)}")
        return jsonify({
            "ok": False,
            "error": f"Failed to reload rules: {str(e)}"
        }), 500

@app.get("/api/rules")
def get_rules():
    """Get current rules (development endpoint)"""
    return jsonify({
        "count": len(RESTAURANT_RULES),
        "rules": RESTAURANT_RULES
    })

if __name__ == '__main__':
    app.run(port=8000, debug=True)
