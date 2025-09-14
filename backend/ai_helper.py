import os
import json
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from typing import Dict, List, Any

# טעינת משתני הסביבה מקובץ .env - חיפוש אוטומטי למעלה בהיררכיה
load_dotenv(find_dotenv())

# יצירת לקוח OpenAI - ייקח את המפתח אוטומטית מ-OPENAI_API_KEY
client = OpenAI()


def create_basic_report(business_data: Dict[str, Any], matching_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """יצירת דוח בסיסי מותאם אישית על בסיס הכללים"""
    
    area = business_data.get('area', 0)
    seats = business_data.get('seats', 0)
    features = business_data.get('features', [])
    
    # Determine complexity based on business characteristics
    complexity = "low"
    complexity_factors = []
    
    if "alcohol" in features:
        complexity = "high"
        complexity_factors.append("הגשת אלכוהול")
    if area > 300 or seats > 100:
        complexity = "high"
        complexity_factors.append("גודל העסק")
    elif area > 150 or seats > 50:
        complexity = "medium"
        complexity_factors.append("גודל בינוני")
    
    if "delivery" in features:
        complexity_factors.append("שליחת מזון")
    if "gas" in features:
        complexity_factors.append("שימוש בגז")
    
    # Estimate time based on complexity and rules
    time_estimates = {
        "low": "2-4 שבועות",
        "medium": "4-8 שבועות", 
        "high": "8-16 שבועות"
    }
    
    # Generate specific actions based on rules - limit to most important ones
    actions = []
    
    # Group rules by category and priority
    categorized_rules = {}
    for rule in matching_rules:
        category = rule['category']
        if category not in categorized_rules:
            categorized_rules[category] = []
        categorized_rules[category].append(rule)
    
    # Select most important rules from each category (limit total to 12 actions max)
    total_actions_limit = 12
    actions_per_category = max(1, total_actions_limit // len(categorized_rules)) if categorized_rules else 1
    
    for category, rules in categorized_rules.items():
        # Sort by title length (shorter titles are usually more general/important)
        sorted_rules = sorted(rules, key=lambda r: len(r['title']))
        selected_rules = sorted_rules[:actions_per_category]  # Limit per category
        
        for rule in selected_rules:
            # Skip rules with unclear or incomplete titles
            if (not rule['title'] or 
                len(rule['title'].strip()) < 10 or 
                '_____' in rule['title'] or
                rule['title'].strip().endswith('.') or
                rule['title'].startswith('שהוא ו') or
                'ואחסנה של מזון.' in rule['title']):
                continue
                
            priority = "medium"
            cost_range = "₪500-1,500"
            professionals = ["יועץ רישוי"]
            
            # Set specific costs and professionals based on rule content
            if "כבאות" in rule['category']:
                if "מערכת" in rule['title'] or "התקנה" in rule['title']:
                    priority = "high"
                    cost_range = "₪3,000-12,000"
                    professionals = ["יועץ בטיחות אש", "מהנדס", "קבלן מוסמך"]
                elif "בדיקה" in rule['title'] or "אישור" in rule['title']:
                    priority = "high"
                    cost_range = "₪800-2,500"
                    professionals = ["יועץ בטיחות אש"]
                else:
                    priority = "medium"
                    cost_range = "₪1,200-3,500"
                    professionals = ["יועץ בטיחות אש"]
                    
            elif "משטרה" in rule['category']:
                if "רישיון" in rule['title']:
                    priority = "high"
                    cost_range = "₪300-800"
                    professionals = ["יועץ רישוי"]
                elif "בדיקה" in rule['title']:
                    priority = "medium"
                    cost_range = "₪200-600"
                    professionals = ["יועץ רישוי"]
                else:
                    priority = "medium"
                    cost_range = "₪400-1,200"
                    professionals = ["יועץ רישוי"]
                    
            elif "בריאות" in rule['category']:
                if "מערכת" in rule['title'] or "התקנה" in rule['title']:
                    priority = "high"
                    cost_range = "₪1,500-5,000"
                    professionals = ["יועץ תברואה", "קבלן מוסמך"]
                elif "בדיקה" in rule['title']:
                    priority = "medium"
                    cost_range = "₪400-1,200"
                    professionals = ["יועץ תברואה"]
                else:
                    priority = "medium"
                    cost_range = "₪600-2,000"
                    professionals = ["יועץ תברואה"]
                    
            elif "גז" in rule['category']:
                priority = "high"
                cost_range = "₪4,000-15,000"
                professionals = ["מתקין גפ\"מ מוסמך", "מהנדס"]
        
            # Create user-friendly explanation instead of technical note
            explanation = ""
            if "כבאות" in rule['category']:
                explanation = "דרישה לבטיחות אש והצלה - יש לקבל אישור מרשויות הכיבוי"
            elif "משטרה" in rule['category']:
                explanation = "דרישה רגולטורית - יש לקבל אישור ממשטרת ישראל"
            elif "בריאות" in rule['category']:
                explanation = "דרישה תברואתית - יש לקבל אישור ממשרד הבריאות"
            elif "גז" in rule['category']:
                explanation = "דרישה לבטיחות גז - יש לקבל אישור ממתקין גפ\"מ מוסמך"
            else:
                explanation = "דרישה רגולטורית לקבלת רישיון העסק"

            actions.append({
                "title": rule['title'],
                "priority": priority,
                "category": rule['category'],
                "based_on_rule_id": rule.get('id', ''),
                "required_professionals": professionals,
                "estimated_cost_range": cost_range,
                "explanation": explanation
            })
    
    # Generate relevant tips based on features
    tips = []
    if "delivery" in features:
        tips.append({
            "category": "שליחת מזון",
            "tip": "הכן אזור ייעודי לשליחת מזון עם ציוד קירור מתאים",
            "benefit": "עמידה בדרישות משרד הבריאות ומניעת קנסות"
        })
    
    if "gas" in features:
        tips.append({
            "category": "בטיחות גז",
            "tip": "בצע בדיקות תקינות גז כל 6 חודשים",
            "benefit": "מניעת תאונות ועמידה בדרישות החוק"
        })
    
    if area <= 150 and seats <= 50:
        tips.append({
            "category": "כבאות",
            "tip": "אתה זכאי למסלול תצהיר מפושט - נצל את היתרון",
            "benefit": "חיסכון בזמן ובעלויות בהליך הרישוי"
        })
    
    # Always add general tips
    tips.extend([
        {
            "category": "תכנון",
            "tip": "התחל בתהליך הרישוי לפני השלמת העבודות",
            "benefit": "חיסכון בזמן ומניעת עיכובים"
        },
        {
            "category": "תיעוד",
            "tip": "שמור את כל המסמכים והאישורים במקום נגיש",
            "benefit": "הקלה בביקורות ובחידוש רישיונות"
        }
    ])
    
    # Generate potential risks
    risks = [
        {
            "risk_type": "רגולטורי",
            "description": "עיכובים בקבלת אישורים מהרשויות",
            "impact": "medium",
            "mitigation": "התחלה מוקדמת של התהליך ומעקב שוטף"
        }
    ]
    
    if "gas" in features:
        risks.append({
            "risk_type": "בטיחותי",
            "description": "סיכוני בטיחות הקשורים לשימוש בגז",
            "impact": "high",
            "mitigation": "התקנה מקצועית ובדיקות תקופתיות"
        })
    
    if "alcohol" in features:
        risks.append({
            "risk_type": "רגולטורי",
            "description": "דרישות מחמירות של המשטרה להגשת אלכוהול",
            "impact": "high",
            "mitigation": "התייעצות עם יועץ מומחה ועמידה קפדנית בדרישות"
        })
    
    # Generate budget planning
    fixed_costs = ["אגרות רישוי", "בדיקות מקצועיות", "שילוט בטיחות"]
    recurring_costs = ["חידוש רישיונות", "בדיקות תקופתיות"]
    optional_costs = ["שדרוגי בטיחות נוספים", "ייעוץ מקצועי מתמשך"]
    
    if "gas" in features:
        fixed_costs.extend(["התקנת מערכת גז", "מערכת כיבוי למנדפים"])
        recurring_costs.append("בדיקות גז תקופתיות")
    
    if "delivery" in features:
        fixed_costs.extend(["ציוד קירור לשליחות", "אזור אריזה"])
        recurring_costs.append("תחזוקת ציוד קירור")
    
    return {
        "summary": {
            "assessment": f"עסק {'קטן' if complexity == 'low' else 'בינוני' if complexity == 'medium' else 'גדול'} בגודל {area} מ\"ר עם {seats} מקומות ישיבה. נדרשת עמידה בדרישות רגולטוריות מרכזיות.",
            "complexity_level": complexity,
            "estimated_time": time_estimates[complexity],
            "key_challenges": complexity_factors if complexity_factors else ["עמידה בדרישות בסיסיות"]
        },
        "actions": actions,
        "potential_risks": risks,
        "tips": tips,
        "open_questions": [
            "האם יש דרישות מיוחדות מהרשות המקומית?",
            "האם העסק ממוקם באזור מוגבל או מיוחד?"
        ],
        "budget_planning": {
            "fixed_costs": fixed_costs,
            "recurring_costs": recurring_costs,
            "optional_costs": optional_costs
        }
    }


def generate_ai_report(business_data: Dict[str, Any], matching_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """יצירת דוח AI מותאם אישית עם ניתוח מעמיק ומעשי"""
    
    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    print("🔑 API Key loaded:", bool(api_key))
    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ אין חיבור ל-ChatGPT - לא יוצג דוח AI")
        return None  # אין AI - אין דוח
    
    try:
        print(f"🤖 Starting AI report generation for business: {business_data['area']}m², {business_data['seats']} seats, features: {business_data['features']}")
        
        # יצירת רשימת דרישות מפורטת
        rules_text = "\n".join([
            f"- {rule['category']}: {rule['title']}\n  {rule.get('note', '')}"
            for rule in matching_rules
        ])
        print(f"📋 Processing {len(matching_rules)} regulatory rules")

        prompt = f"""אתה יועץ מומחה לרישוי עסקים בישראל עם 15 שנות ניסיון. תפקידך לנתח את פרטי העסק ולהכין דוח מקצועי ומותאם אישית.

🏢 **פרטי העסק:**
- סוג: מסעדה/בית אוכל  
- שטח: {business_data['area']} מ"ר
- מקומות ישיבה: {business_data['seats']}
- מאפיינים מיוחדים: {', '.join(business_data['features'])}

📋 **דרישות רגולטוריות רלוונטיות:**
{rules_text}

🎯 **משימתך:**
צור דוח מקצועי המתאים בדיוק לעסק הזה, עם דגש על:
1. ניתוח מעמיק של המורכבות והאתגרים
2. פעולות קונקרטיות עם לוחות זמנים ועלויות מדויקות
3. זיהוי סיכונים ודרכי מניעה
4. טיפים מעשיים לחיסכון בזמן ובעלות
5. תכנון תקציב מפורט

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
        "fixed_costs": ["התקנת מערכת גז: 15,000-25,000 ש״ח", "ייעוץ רישוי עסק: 3,000-5,000 ש״ח", "אישורי בטיחות: 2,000-4,000 ש״ח"],
        "recurring_costs": ["תחזוקה שנתית למערכות בטיחות: 2,000-4,000 ש״ח", "ביטוח עסקי: 3,000-8,000 ש״ח לשנה", "אגרות רישוי שנתיות: 500-1,500 ש״ח"],
        "optional_costs": ["שדרוג ציוד מטבח: 20,000-50,000 ש״ח", "מערכת אזעקה מתקדמת: 5,000-10,000 ש״ח", "פרסום ושיווק: 5,000-15,000 ש״ח"]
    }}
}}

חשוב:
1. כל הפעולות והטיפים חייבים להיות ספציפיים, מדידים וישימים
2. יש לתעדף פעולות לפי דחיפות וחשיבות
3. עלויות צריכות להיות מציאותיות ומבוססות על מחירי השוק הישראלי
4. אין להמציא דרישות שלא מופיעות בכללים
5. יש להתייחס לכל המאפיינים המיוחדים של העסק
6. **חובה לכלול מחירים ספציפיים בש״ח בכל פריט בתכנון התקציב - לא רק תיאורים כלליים!**
7. השתמש בטווחי מחירים מציאותיים (למשל: "התקנת מערכת גז: 15,000-25,000 ש״ח")"""

        print("🚀 Sending request to OpenAI...")
        print(f"📝 Prompt length: {len(prompt)} characters")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "אתה יועץ מומחה לרישוי עסקים בישראל עם ניסיון רב. תחזיר תמיד JSON תקין בלבד, ללא טקסט נוסף."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        print("✅ Got response from OpenAI")
        print(f"💰 Token usage - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
        
        try:
            print("Parsing response...")
            raw_content = response.choices[0].message.content
            print(f"🔍 Raw AI response (first 500 chars): {raw_content[:500]}...")
            
            # Clean up common JSON issues from AI responses
            cleaned_content = raw_content.strip()
            
            # Fix common Hebrew text issues that break JSON
            import re
            # Replace all problematic quotes in Hebrew text with safe alternatives
            cleaned_content = re.sub(r'(\w)"(\w)', r'\1״\2', cleaned_content)  # Hebrew quotes between letters
            cleaned_content = cleaned_content.replace('מ"ר', 'מ״ר')  # Specific cases
            cleaned_content = cleaned_content.replace('ת"י', 'ת״י')  
            cleaned_content = cleaned_content.replace('גפ"מ', 'גפ״מ')
            cleaned_content = cleaned_content.replace('ש"ח', 'ש״ח')  # Shekels
            cleaned_content = cleaned_content.replace('ק"ג', 'ק״ג')  # Kilograms
            
            # Remove any markdown code blocks if present
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content.replace('```json', '').replace('```', '').strip()
            elif cleaned_content.startswith('```'):
                cleaned_content = cleaned_content.replace('```', '').strip()
            
            print(f"🧹 Cleaned content (first 500 chars): {cleaned_content[:500]}...")
            ai_response = json.loads(cleaned_content)
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
        print(f"❌ OpenAI API error: {error_message}")
        
        # Log more details for debugging
        if hasattr(e, 'response'):
            print(f"🔍 API Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'Unknown'}")
        
        # Return the basic report instead of showing technical errors to users
        print("❌ שגיאה בחיבור ל-ChatGPT - לא יוצג דוח AI")
        return None  # אין AI - אין דוח