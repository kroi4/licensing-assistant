import os
from dotenv import load_dotenv
from openai import OpenAI
import json

def test_openai_connection():
    # טעינת משתני הסביבה
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    print(f"API Key exists and not empty: {bool(api_key)}")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}]
        )
        print("\nOpenAI Connection Success!")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"\nError connecting to OpenAI: {str(e)}")
        return False

def generate_ai_report(business_data, matching_rules):
    prompt = f"""
    אתה יועץ רישוי עסקים. קיבלת את נתוני העסק:
    שטח: {business_data['area']} מ"ר
    מקומות ישיבה: {business_data['seats']}
    מאפיינים: {', '.join(business_data['features'])}

    דרישות רגולטוריות רלוונטיות:
    {chr(10).join([f"- {r['category']}: {r['title']} ({r['status']})" for r in matching_rules])}

    נא לנסח דוח קצר וברור בעברית, כולל:
    - סיכום כללי
    - רשימת פעולות נדרשות (לפי סדר חשיבות)
    - טיפים והמלצות
    - אם חסר מידע, ציין זאת ב-open_questions

    החזר JSON במבנה:
    {{
      "summary": "...",
      "actions": [{{"title": "...", "priority": "high|med|low", "based_on_rule_id": "...", "explanation": "..."}}],
      "tips": ["..."],
      "open_questions": []
    }}
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "אתה יועץ רישוי. אל תוסיף דרישות. אם חסר מידע → open_questions."},
            {"role": "user", "content": prompt}
        ]
    )
    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    test_openai_connection()