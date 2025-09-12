import json, os
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Session, Rule, AssessmentLog

# 1) יוצרים את האפליקציה לפני שקוראים ל-CORS
app = Flask(__name__, static_folder="static", static_url_path="")
app.config['JSON_AS_ASCII'] = False
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173","http://127.0.0.1:5173"]}})

HERE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(HERE, "rules", "restaurant_rules.json")

def load_rules() -> List[Dict[str, Any]]:
    session = Session()
    rules = session.query(Rule).all()
    result = [{
        'id': rule.id,
        'category': rule.category,
        'title': rule.title,
        'status': rule.status,
        'note': rule.note,
        'if': rule.conditions
    } for rule in rules]
    session.close()
    return result

RESTAURANT_RULES = load_rules()

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
    matched = []
    for rule in RESTAURANT_RULES:
        if rule_matches(rule.get("if", {}), payload):
            matched.append({
                "id": rule["id"],
                "category": rule["category"],
                "title": rule["title"],
                "status": rule["status"],
                "note": rule.get("note", "")
            })
    summary = {
        "type": "restaurant",
        "area": payload.get("area"),
        "seats": payload.get("seats"),
        "features": payload.get("features", [])
    }
    return {"checklist": matched, "summary": summary}

@app.get("/")
def index():
    return app.send_static_file("index.html")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/assess")
def assess():
    data = request.get_json(silent=True) or {}
    errors = {}
    try:
        area = float(data.get("area", ""));  assert area > 0
    except Exception:
        errors["area"] = "area must be > 0 (number)"
    try:
        seats = int(data.get("seats", ""));  assert seats >= 0
    except Exception:
        errors["seats"] = "seats must be >= 0 (integer)"
    features = data.get("features")
    if not isinstance(features, list) or not features:
        errors["features"] = "features must be a non-empty list"
    if errors:
        return jsonify({"error": "validation_error", "details": errors}), 400

    payload = {"area": area, "seats": seats, "features": features}
    result = evaluate_restaurant(payload)
    
    # שמירת הבקשה והתוצאות
    session = Session()
    log = AssessmentLog(
        area=payload["area"],
        seats=payload["seats"],
        features=payload["features"],
        results=result
    )
    session.add(log)
    session.commit()
    session.close()
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=True)
