// A numbered section of the story: heading, one-sentence takeaway, then the charts.
export default function Chapter({ number, title, lead, children }) {
  return (
    <section className="chapter">
      <header className="chapter-head">
        <span className="chapter-no">{String(number).padStart(2, "0")}</span>
        <div>
          <h2>{title}</h2>
          {lead && <p className="lead">{lead}</p>}
        </div>
      </header>
      <div className="chapter-body">{children}</div>
    </section>
  );
}
