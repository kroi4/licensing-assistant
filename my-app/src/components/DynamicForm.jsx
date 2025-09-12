import { useState } from "react";

export default function DynamicForm({ schema, onSubmit }) {
  // הכנת מצב התחלתי לפי השדות
  const initial = {};
  schema.fields.forEach(f => {
    if (f.type === "checkbox-group") initial[f.name] = []; // מערך ערכים מסומנים
    else initial[f.name] = "";
  });

  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});

  function setField(name, val) {
    setValues(v => ({ ...v, [name]: val }));
  }

  function toggleCheckbox(name, optionValue) {
    setValues(v => {
      const current = new Set(v[name]);
      current.has(optionValue) ? current.delete(optionValue) : current.add(optionValue);
      return { ...v, [name]: Array.from(current) };
    });
  }

  function validate() {
    const e = {};
    for (const f of schema.fields) {
      const val = values[f.name];

      if (f.type === "number") {
        const n = Number(val);
        if (f.required && (val === "" || Number.isNaN(n))) e[f.name] = "שדה חובה";
        else if (!Number.isNaN(n)) {
          if (f.min != null && n < f.min) e[f.name] = `ערך חייב להיות ≥ ${f.min}`;
          if (f.max != null && n > f.max) e[f.name] = `ערך חייב להיות ≤ ${f.max}`;
        }
      }

      if (f.type === "checkbox-group") {
        if (f.required && (!Array.isArray(val) || val.length === 0)) {
          e[f.name] = "בחר/י לפחות מאפיין אחד";
        }
        if (f.minSelected && Array.isArray(val) && val.length < f.minSelected) {
          e[f.name] = `בחר/י לפחות ${f.minSelected}`;
        }
      }

      if (f.type === "text" && f.required && !val) {
        e[f.name] = "שדה חובה";
      }
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function submit(ev) {
    ev.preventDefault();
    if (!validate()) return;

    // נרמול מספרים
    const normalized = { ...values };
    schema.fields.forEach(f => {
      if (f.type === "number") normalized[f.name] = Number(values[f.name]);
    });

    onSubmit(normalized);
  }

  return (
    <form className="card" onSubmit={submit} noValidate>
      {schema.fields.map(f => (
        <div key={f.name} style={{ marginTop: 12 }}>
          {f.type === "number" && (
            <label>
              {f.label}
              <input
                type="number"
                inputMode="numeric"
                value={values[f.name]}
                onChange={(e) => setField(f.name, e.target.value)}
                min={f.min}
                max={f.max}
                required={f.required}
              />
              {errors[f.name] && <div className="error">{errors[f.name]}</div>}
            </label>
          )}

          {f.type === "text" && (
            <label>
              {f.label}
              <input
                type="text"
                value={values[f.name]}
                onChange={(e) => setField(f.name, e.target.value)}
                required={f.required}
              />
              {errors[f.name] && <div className="error">{errors[f.name]}</div>}
            </label>
          )}

          {f.type === "checkbox-group" && (
            <fieldset style={{ border: "none", padding: 0 }}>
              <legend style={{ fontWeight: 600 }}>{f.label}</legend>
              {f.options.map(opt => (
                <label key={opt.value} style={{ display: "block", marginTop: 6 }}>
                  <input
                    type="checkbox"
                    checked={values[f.name].includes(opt.value)}
                    onChange={() => toggleCheckbox(f.name, opt.value)}
                  />{" "}
                  {opt.label}
                </label>
              ))}
              {errors[f.name] && <div className="error">{errors[f.name]}</div>}
            </fieldset>
          )}
        </div>
      ))}

      <button type="submit" style={{ marginTop: 16 }}>צור דוח</button>
    </form>
  );
}
