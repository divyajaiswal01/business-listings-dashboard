// Shared frame for every chart: title, subtitle, optional note, and loading / empty states.
export default function ChartCard({ title, subtitle, note, loading, empty, wide, children }) {
  return (
    <section className={wide ? "card wide" : "card"}>
      <header className="card-head">
        <h3>{title}</h3>
        {subtitle && <p>{subtitle}</p>}
      </header>
      <div className="card-body">
        {loading ? (
          <div className="placeholder">Loading…</div>
        ) : empty ? (
          <div className="placeholder">Nothing to show for these filters.</div>
        ) : (
          children
        )}
      </div>
      {note && !loading && !empty && <p className="card-note">{note}</p>}
    </section>
  );
}
