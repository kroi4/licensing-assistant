import { useState } from "react";
import { businessTypes } from "./config/businessTypes.js";
import DynamicForm from "./components/DynamicForm.jsx";

export default function App() {
  const [bizType, setBizType] = useState("restaurant"); // ברירת מחדל: מסעדה
  const [input, setInput] = useState(null);
  const [result, setResult] = useState(null);

  const schema = businessTypes[bizType];

  const handleSubmit = async (values) => {
    // שמירה להצגה וסיכום
    const payload = { type: bizType, ...values };
    setInput(payload);

    // TODO: קריאה אמיתית ל-Backend (Flask)
    // const res = await fetch("http://127.0.0.1:8000/api/assess", { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(payload) });
    // const data = await res.json();
    // setResult(data);

    // דמו: "מנוע התאמה" בסיסי + דוח AI דמה
    const checklist = [];
    if ((values.features || []).includes("gas")) {
      checklist.push({ category: "גז", title: "אישור מתקין גז", status: "חובה", note: "נבחר 'שימוש בגז'" });
    }
    if (values.area >= 100) {
      checklist.push({ category: "בטיחות", title: "מטף נוסף ותוכנית פינוי", status: "חובה", note: "שטח ≥ 100 מ״ר" });
    }
    if (values.seats >= 50) {
      checklist.push({ category: "כיבוי אש", title: "אישור מתקדם", status: "חובה", note: "תפוסה ≥ 50" });
    }

    const featuresText = (values.features || []).map(v => ({gas:"שימוש בגז",meat:"הגשת בשר",delivery:"משלוחים"}[v])).join(", ") || "—";
    const aiReport = [
      "דוח חכם (דמה):",
      `• סוג עסק: מסעדה`,
      `• גודל: ${values.area} מ״ר, תפוסה: ${values.seats}, מאפיינים: ${featuresText}`,
      "• עדיפויות פעולה:",
      "  1) הסדרת בטיחות אש בהתאם לתפוסה והשטח",
      "  2) התאמת תשתיות גז (אם נבחר גז)",
      "  3) תיעוד תברואה ואישורים שוטפים",
    ].join("\n");

    setResult({ checklist, aiReport });
  };

  return (
    <main className="container">
      <h1>מערכת הערכת רישוי לעסקים</h1>
      <p className="subtitle">כרגע נתמכות מסעדות; שאר הסוגים יוצגו בקרוב.</p>

      <div className="card" style={{ marginBottom: 12 }}>
        <label>סוג עסק
          <select value={bizType} onChange={(e)=>setBizType(e.target.value)}>
            {Object.entries(businessTypes).map(([key, cfg]) => (
              <option key={key} value={key} disabled={cfg.disabled}>{cfg.label}</option>
            ))}
          </select>
        </label>
      </div>

      <DynamicForm schema={schema} onSubmit={handleSubmit} />

      {input && result && (
        <div className="card">
          <h2>תוצאות</h2>
          <h3>סיכום קלט</h3>
          <ul>
            {"area" in input && <li>גודל: {input.area} מ״ר</li>}
            {"seats" in input && <li>תפוסה: {input.seats}</li>}
            {Array.isArray(input.features) && <li>מאפיינים: {input.features.map(v => ({gas:"שימוש בגז", meat:"הגשת בשר", delivery:"משלוחים"}[v])).join(", ") || "—"}</li>}
          </ul>

          <h3>צ׳ק-ליסט דרישות</h3>
          <ul>
            {result.checklist.length === 0 && <li>לא נמצאו דרישות נוספות לפי הקלט.</li>}
            {result.checklist.map((it, i) => (
              <li key={i}><strong>{it.category} — {it.title}</strong> · {it.status} · {it.note}</li>
            ))}
          </ul>

          <h3>דוח חכם (AI)</h3>
          <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{result.aiReport}</pre>
        </div>
      )}
    </main>
  );
}
