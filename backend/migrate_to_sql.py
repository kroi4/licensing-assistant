import json
from models import Base, engine, Session, Rule

def migrate_data():
    # יצירת הטבלאות
    Base.metadata.create_all(engine)
    
    # קריאת הנתונים מ-JSON
    rules_data = [
        {
            "id": "gas-cert",
            "category": "גז",
            "title": "אישור מתקין גז מוסמך",
            "status": "חובה",
            "note": "נדרש כאשר יש שימוש בגז",
            "conditions": {"features_any": ["gas"]}
        },
        {
            "id": "fire-over-50",
            "category": "כיבוי אש",
            "title": "אישור כיבוי אש מתקדם",
            "status": "חובה",
            "note": "תפוסה ≥ 50",
            "conditions": {"seats_min": 50}
        },
        {
            "id": "area-over-100",
            "category": "בטיחות",
            "title": "מטף נוסף ותכנית פינוי",
            "status": "חובה",
            "note": "שטח ≥ 100 מ״ר",
            "conditions": {"area_min": 100}
        },
        {
            "id": "meat-handling",
            "category": "תברואה",
            "title": "נהלי טיפול בבשר ותיעוד ספקים",
            "status": "חובה",
            "note": "נדרש כאשר מוגש בשר",
            "conditions": {"features_any": ["meat"]}
        },
        {
            "id": "delivery-labels",
            "category": "שילוט/תפעול",
            "title": "סימון אלרגנים ואריזות בטוחות למשלוחים",
            "status": "מומלץ",
            "note": "רלוונטי למשלוחים",
            "conditions": {"features_any": ["delivery"]}
        }
    ]
    
    session = Session()
    
    # הכנסת הנתונים ל-SQL
    for rule_data in rules_data:
        conditions = rule_data.pop('conditions', {})
        rule = Rule(
            id=rule_data['id'],
            category=rule_data['category'],
            title=rule_data['title'],
            status=rule_data['status'],
            note=rule_data['note'],
            conditions=conditions
        )
        session.add(rule)
    
    session.commit()
    session.close()

if __name__ == "__main__":
    migrate_data()