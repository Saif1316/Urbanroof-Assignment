const SEVERITY_STYLES = {
  high: { color: "var(--color-severity-high)", label: "High" },
  medium: { color: "var(--color-severity-medium)", label: "Medium" },
  low: { color: "var(--color-severity-low)", label: "Low" },
  "not available": { color: "var(--color-muted)", label: "Not Available" },
};

export default function SeverityBadge({ level }) {
  const key = (level || "").toLowerCase().trim();
  const style = SEVERITY_STYLES[key] || SEVERITY_STYLES["not available"];

  return (
    <span
      className="severity-badge"
      style={{ borderColor: style.color, color: style.color }}
    >
      <span className="severity-dot" style={{ backgroundColor: style.color }} />
      {style.label}
    </span>
  );
}
