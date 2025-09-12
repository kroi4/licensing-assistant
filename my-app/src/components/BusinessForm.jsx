import { useState } from "react";

export default function BusinessForm({ onSubmit }) {
  const [area, setArea] = useState("");
  const [seats, setSeats] = useState("");
  const [features, setFeatures] = useState({ gas:false, meat:false, delivery:false });
  const [errors, setErrors] = useState({});

  function toggleFeature(name) {
    setFeatures(f => ({ ...f, [name]: !f[name] }));
  }

  function validate() {
    const e = {};
    const a = Number(area);
    const s = Number(seats);
    if (!area || isNaN(a) || a <= 0) e.area = "חובה להזין גודל חיובי";
    if (seats === "" || isNaN(s) || s < 0) e.seats = "מספר מקומות לא תקין";
    const anyFeature = Object.values(features).some(Boolean);
    if (!anyFeature) e.features = "בחר/י לפחות מאפיין אחד";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function submit(ev) {
    ev.preventDefault();
    if (!validate()) return;
    const selected = Object.entries(features)
      .filter(([,v]) => v)
      .map(([k]) => k); // ["gas","meat",...]
    onSubmit({ area: Number(area), seats: Number(seats), features: selected });
  }

  return (
    <form className="card" onSubmit={submit} noValidate>
      <label>גודל העסק (מ"ר)
        <input
          type="number" inputMode="numeric" placeholder="לדוגמה: 85"
          value={area} onChange={(e)=>setArea(e.target.value)}
        />
        {errors.area && <div className="error">{errors.area}</div>}
      </label>

      <label>מספר מקומות ישיבה / תפוסה
        <input
          type="number" inputMode="numeric" placeholder="למשל: 40"
          value={seats} onChange={(e)=>setSeats(e.target.value)}
        />
        {errors.seats && <div className="error">{errors.seats}</div>}
      </label>

      <fieldset style={{ border:"none", padding:0, marginTop:12 }}>
        <legend style={{ fontWeight:600, marginBottom:6 }}>מאפיינים (לפחות אחד)</legend>
        <label><input type="checkbox" checked={features.gas} onChange={()=>toggleFeature("gas")} /> שימוש בגז</label>
        <label><input type="checkbox" checked={features.meat} onChange={()=>toggleFeature("meat")} /> הגשת בשר</label>
        <label><input type="checkbox" checked={features.delivery} onChange={()=>toggleFeature("delivery")} /> משלוחים</label>
        {errors.features && <div className="error">{errors.features}</div>}
      </fieldset>

      <button type="submit">צור דוח</button>
    </form>
  );
}
