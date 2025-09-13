# 🏪 מערכת הערכת רישוי עסקים - הוראות הרצה

## סטטוס הפרויקט ✅

המערכת מוכנה להרצה! השרת Backend רץ בהצלחה והFrontend פונקציונלי.

## דרישות מקדימות

- Python 3.12+ מותקן
- Virtual environment מוכן (venv)
- כל ה-dependencies מותקנים

## הרצת המערכת

### 1. הפעלת השרת Backend

```powershell
# מהתיקייה הראשית של הפרויקט
.\venv\Scripts\Activate.ps1
cd backend
python app.py
```

השרת יעלה על: `http://localhost:8000`

### 2. פתיחת Frontend

פתח את הקובץ `frontend/index.html` בדפדפן או השתמש בפקודה:

```powershell
Start-Process "frontend/index.html"
```

## בדיקת תקינות המערכת

### בדיקת השרת
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
```

תשובה מצופה: `{"status": "ok"}`

### בדיקת API
```powershell
$body = '{"area": 100, "seats": 50, "features": ["gas", "delivery"]}'
Invoke-WebRequest -Uri "http://localhost:8000/api/assess" -Method POST -Body $body -ContentType "application/json"
```

## מאפיינים זמינים במערכת

- ✅ **שרת Backend Flask** - רץ על פורט 8000
- ✅ **Frontend HTML/CSS/JS** - ממשק משתמש מותאם לעברית
- ✅ **API להערכת רישוי** - `/api/assess`
- ✅ **מנוע התאמת כללים** - לוגיקה מובנית לדרישות רגולטוריות
- ⚠️ **אינטגרציה עם AI** - דורש מפתח OpenAI API

## הגדרת מפתח OpenAI (אופציונלי)

ליצירת דוחות AI מותאמים אישית:

1. קבל מפתח API מ-OpenAI
2. צור קובץ `.env` בתיקיית `backend`:
```
OPENAI_API_KEY=your_api_key_here
```

**הערה:** המערכת עובדת גם ללא מפתח AI - תקבל דוח בסיסי במקום דוח AI.

## פונקציונליות המערכת

### קלט נתמך:
- **שטח** (מ"ר) - מספר חיובי
- **מקומות ישיבה** - מספר שלם >= 0
- **מאפיינים מיוחדים:**
  - שימוש בגז (`gas`)
  - שירות משלוחים (`delivery`) 
  - הגשת אלכוהול (`alcohol`)
  - מנדף מטבח מקצועי (`hood`)

### פלט המערכת:
- **סיכום כללי** - מאפייני העסק ומסלולי רישוי
- **רשימת דרישות רגולטוריות** - כללים רלוונטיים לפי המאפיינים
- **דוח AI מותאם** (אם מוגדר מפתח) - ניתוח מעמיק והמלצות

## פתרון בעיות נפוצות

### השרת לא עולה
```powershell
# וודא שה-virtual environment פעיל
.\venv\Scripts\Activate.ps1

# בדוק שאתה בתיקיית backend
cd backend
python app.py
```

### שגיאות CORS בדפדפן
השרת מוגדר לקבל בקשות מ-localhost. וודא שאתה פותח את הHTML מקומית.

### שגיאת AI
אם אין מפתח OpenAI, המערכת תחזיר דוח בסיסי. זה נורמלי ולא משפיע על הפונקציונליות הבסיסית.

## מבנה הפרויקט

```
licensing-assistant/
├── backend/
│   ├── app.py              # שרת Flask ראשי
│   ├── ai_helper.py        # מודול אינטגרציה עם OpenAI
│   ├── models.py           # מודלים (אם נדרש)
│   └── rules/              # כללי רישוי
├── frontend/
│   ├── index.html          # ממשק משתמש
│   ├── style.css           # עיצוב
│   └── script.js           # לוגיקת Frontend
├── venv/                   # Virtual environment
├── requirements.txt        # Dependencies
└── README.md              # תיעוד

```

## סטטוס הפיתוח

- ✅ Backend מוכן ופונקציונלי
- ✅ Frontend מוכן ופונקציונלי  
- ✅ API עובד ומחזיר תוצאות
- ✅ מנוע כללים פועל
- ⚠️ AI דורש הגדרת מפתח
- ✅ ממשק משתמש מותאם לעברית
- ✅ עיצוב רספונסיבי

המערכת מוכנה לשימוש ובדיקה! 🎉
