export default function ResultCard({ data, report }) {
  if (!data) return null;
  const labels = { gas:"שימוש בגז", meat:"הגשת בשר", delivery:"משלוחים" };
  const feats = data.features?.length ? data.features.map(f => labels[f]).join(", ") : "—";

  return (
    <div className="card">
      <h2>סיכום קלט</h2>
      <ul>
        <li>גודל: {data.area} מ"ר</li>
        <li>תפוסה: {data.seats}</li>
        <li>מאפיינים: {feats}</li>
      </ul>
      {report && (
        <>
          <h3>טיוטת דוח (דמה)</h3>
          <p>{report}</p>
        </>
      )}
    </div>
  );
}
