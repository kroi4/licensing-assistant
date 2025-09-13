# backend/app.py
import os
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_helper import generate_ai_report

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
# Configure CORS to allow all origins (for development)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# --- כללי: מאפייני קלט נתמכים ---
# features אפשריים: "gas", "delivery", "alcohol", "hood"
# area (float > 0), seats (int >= 0)

RESTAURANT_RULES: List[Dict[str, Any]] = [
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
        "if": {"features_any": ["gas", "hood"]}
    }
]

def translate_features(features: List[str]) -> List[str]:
    """תרגום מאפיינים מאנגלית לעברית"""
    feature_translations = {
        "gas": "שימוש בגז",
        "delivery": "שירות משלוחים", 
        "alcohol": "הגשת אלכוהול",
        "hood": "מנדף מטבח מקצועי"
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

    # 4. הפקת דו"ח AI (אופציונלי)
    try:
        ai_report = generate_ai_report(payload, matched_rules)
        result['ai_report'] = ai_report
    except Exception as e:
        print(f"AI error: {str(e)}")
        result['ai_report'] = {
            "summary": {
                "assessment": "לא ניתן היה ליצור דוח AI",
                "complexity_level": "unknown",
                "estimated_time": "לא ניתן להעריך",
                "key_challenges": ["תקלה בשירות ה-AI"]
            },
            "actions": [],
            "potential_risks": [],
            "tips": [],
            "open_questions": ["נא לפנות לתמיכה"],
            "budget_planning": {
                "fixed_costs": [],
                "recurring_costs": [],
                "optional_costs": []
            }
        }

    return result

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@app.post("/api/assess")
def assess():
    try:
        data = request.get_json(silent=True) or {}
        
        if not all(k in data for k in ['area', 'seats', 'features']):
            return jsonify({"error": "חסרים שדות חובה"}), 400
        
        # Log the received data for debugging
        print(f"Received data: {data}")
        
        result = evaluate_restaurant(data)
        
        # Log the result for debugging
        print(f"Evaluation result: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in assess endpoint: {str(e)}")
        return jsonify({"error": f"שגיאה בעיבוד הבקשה: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=8000, debug=True)
