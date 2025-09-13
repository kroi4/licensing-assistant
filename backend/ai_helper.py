import os
import json
from dotenv import load_dotenv
import openai
from typing import Dict, List, Any

# טעינת משתני הסביבה מקובץ .env
load_dotenv()

# יצירת לקוח OpenAI - גרסה ישנה
openai.api_key = os.getenv('OPENAI_API_KEY')


def generate_ai_report(business_data: Dict[str, Any], matching_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """יצירת דוח AI מותאם אישית עם ניתוח מעמיק ומעשי"""
    try:
        print("Starting AI report generation...")
        print(f"API Key exists: {bool(os.getenv('OPENAI_API_KEY'))}")
        
        # יצירת רשימת דרישות מפורטת
        rules_text = "\n".join([
            f"- {rule['category']}: {rule['title']}\n  {rule.get('note', '')}"
            for rule in matching_rules
        ])

        prompt = f"""אתה יועץ בכיר לרישוי עסקים בישראל. נתח את המידע הבא ותן המלצות מעשיות וקונקרטיות.

פרטי העסק:
- סוג: מסעדה/בית אוכל
- שטח: {business_data['area']} מ"ר
- מקומות ישיבה: {business_data['seats']}
- מאפיינים: {', '.join(business_data['features'])}

דרישות רגולטוריות רלוונטיות:
{rules_text}

נדרש להחזיר JSON במבנה המדויק הבא:
{{
    "summary": {{
        "assessment": "הערכה כללית של מורכבות התהליך והנקודות העיקריות",
        "complexity_level": "high/medium/low",
        "estimated_time": "הערכת זמן משוערת לקבלת הרישיון",
        "key_challenges": ["אתגר 1", "אתגר 2"]
    }},
    "actions": [
        {{
            "title": "כותרת הפעולה - ספציפית ומדידה",
            "priority": "high/medium/low",
            "category": "תשתית/בטיחות/תברואה/מסמכים",
            "based_on_rule_id": "מזהה הכלל הרלוונטי",
            "required_professionals": ["אנשי מקצוע נדרשים"],
            "estimated_cost_range": "טווח עלויות משוער",
            "explanation": "הסבר מפורט כולל דגשים ספציפיים"
        }}
    ],
    "potential_risks": [
        {{
            "risk_type": "תפעולי/בטיחותי/רגולטורי",
            "description": "תיאור הסיכון",
            "impact": "high/medium/low",
            "mitigation": "דרכי התמודדות מומלצות"
        }}
    ],
    "tips": [
        {{
            "category": "תכנון/בטיחות/תפעול",
            "tip": "טיפ מעשי וספציפי",
            "benefit": "התועלת/החיסכון מיישום הטיפ"
        }}
    ],
    "open_questions": ["שאלות שצריך לברר - רק אם באמת חסר מידע מהותי"],
    "budget_planning": {{
        "fixed_costs": ["עלויות חד פעמיות צפויות"],
        "recurring_costs": ["עלויות שוטפות/תקופתיות"],
        "optional_costs": ["עלויות אופציונליות לשיפור/ייעול"]
    }}
}}

חשוב:
1. כל הפעולות והטיפים חייבים להיות ספציפיים, מדידים וישימים
2. יש לתעדף פעולות לפי דחיפות וחשיבות
3. עלויות צריכות להיות מציאותיות ומבוססות על מחירי השוק
4. אין להמציא דרישות שלא מופיעות בכללים
5. יש להתייחס לכל המאפיינים המיוחדים של העסק"""

        print("Sending request to OpenAI...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "אתה יועץ מומחה לרישוי עסקים בישראל. ענה ב-JSON בלבד."},
                {"role": "user", "content": prompt}
            ]
        )
        print("Got response from OpenAI")
        
        try:
            print("Parsing response...")
            ai_response = json.loads(response.choices[0].message['content'])
            print("Response parsed successfully")
            
            # וידוא תקינות המבנה ומילוי ערכי ברירת מחדל אם צריך
            validated_response = {
                "summary": {
                    "assessment": ai_response.get("summary", {}).get("assessment", "לא סופק ניתוח"),
                    "complexity_level": ai_response.get("summary", {}).get("complexity_level", "medium"),
                    "estimated_time": ai_response.get("summary", {}).get("estimated_time", "לא סופקה הערכה"),
                    "key_challenges": ai_response.get("summary", {}).get("key_challenges", [])
                },
                "actions": [{
                    "title": action.get("title", ""),
                    "priority": action.get("priority", "medium"),
                    "category": action.get("category", "כללי"),
                    "based_on_rule_id": action.get("based_on_rule_id", ""),
                    "required_professionals": action.get("required_professionals", []),
                    "estimated_cost_range": action.get("estimated_cost_range", "לא סופקה הערכה"),
                    "explanation": action.get("explanation", "")
                } for action in ai_response.get("actions", [])],
                "potential_risks": [{
                    "risk_type": risk.get("risk_type", "תפעולי"),
                    "description": risk.get("description", ""),
                    "impact": risk.get("impact", "medium"),
                    "mitigation": risk.get("mitigation", "")
                } for risk in ai_response.get("potential_risks", [])],
                "tips": [{
                    "category": tip.get("category", "כללי"),
                    "tip": tip.get("tip", ""),
                    "benefit": tip.get("benefit", "")
                } for tip in ai_response.get("tips", [])],
                "open_questions": ai_response.get("open_questions", []),
                "budget_planning": {
                    "fixed_costs": ai_response.get("budget_planning", {}).get("fixed_costs", []),
                    "recurring_costs": ai_response.get("budget_planning", {}).get("recurring_costs", []),
                    "optional_costs": ai_response.get("budget_planning", {}).get("optional_costs", [])
                }
            }
            return validated_response
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            raise ValueError("Invalid JSON response from OpenAI")

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        return {
            "summary": {
                "assessment": "שגיאה בעיבוד התשובה מה-AI",
                "complexity_level": "unknown",
                "estimated_time": "לא ניתן להעריך",
                "key_challenges": ["תקלה בפענוח התשובה"]
            },
            "actions": [],
            "potential_risks": [],
            "tips": [],
            "open_questions": ["נא לפנות לתמיכה - שגיאת JSON"],
            "budget_planning": {
                "fixed_costs": [],
                "recurring_costs": [],
                "optional_costs": []
            }
        }
    except Exception as e:
        error_message = str(e)
        print(f"OpenAI API error: {error_message}")
        
        # ניתוח סוג השגיאה וחזרה עם הודעה מתאימה
        if "rate limit" in error_message.lower():
            assessment = "המערכת עמוסה כרגע, נא לנסות שוב בעוד מספר דקות"
        elif "timeout" in error_message.lower():
            assessment = "חיבור לשירות ה-AI נכשל עקב תקלת תקשורת"
        elif "content filter" in error_message.lower():
            assessment = "לא ניתן לעבד את הבקשה עקב מגבלות תוכן"
        else:
            assessment = "אירעה שגיאה בתקשורת עם מערכת ה-AI"
        
        return {
            "summary": {
                "assessment": assessment,
                "complexity_level": "unknown",
                "estimated_time": "לא ניתן להעריך",
                "key_challenges": ["תקלה בשירות ה-AI"]
            },
            "actions": [],
            "potential_risks": [
                {
                    "risk_type": "תפעולי",
                    "description": "תקלה בשירות הניתוח האוטומטי",
                    "impact": "medium",
                    "mitigation": "נא לנסות שוב או לפנות לתמיכה"
                }
            ],
            "tips": [],
            "open_questions": [f"נא לפנות לתמיכה - {error_message}"],
            "budget_planning": {
                "fixed_costs": [],
                "recurring_costs": [],
                "optional_costs": []
            }
        }