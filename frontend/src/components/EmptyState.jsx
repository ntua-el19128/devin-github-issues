export default function EmptyState({ title, description, action }) {
  return (
    <div className="card center" style={{ padding: 32 }}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      {description && <p className="small" style={{ marginTop: 8 }}>{description}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}