
export const businessTypes = {
  restaurant: {
    label: "מסעדה / בית קפה",
    fields: [
      { name: "area",   label: "גודל העסק (מ״ר)", type: "number", min: 1, required: true },
      { name: "seats",  label: "מספר מקומות ישיבה / תפוסה", type: "number", min: 0, required: true },
      {
        name: "features",
        label: "מאפיינים (בחר/י לפחות אחד)",
        type: "checkbox-group",
        required: true,
        minSelected: 1,
        options: [
          { value: "gas",      label: "שימוש בגז" },
          { value: "meat",     label: "הגשת בשר" },
          { value: "delivery", label: "משלוחים" }
        ]
      }
    ]
  },

  // דוגמאות להרחבה עתידית — כרגע מנוטרל/ת:
  retail: {
    label: "חנות קמעונאית (בקרוב)",
    disabled: true,
    fields: [
      { name: "area", label: "גודל (מ״ר)", type: "number", min: 1, required: true }
    ]
  },
  gym: {
    label: "חדר כושר (בקרוב)",
    disabled: true,
    fields: [
      { name: "area", label: "גודל (מ״ר)", type: "number", min: 1, required: true },
      { name: "seats", label: "תפוסה מקסימלית", type: "number", min: 0, required: true }
    ]
  }
};
