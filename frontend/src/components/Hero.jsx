import { pct } from "../insights";

export default function Hero({ summary, sources, findings, loading }) {
  const total = summary?.total_listings;
  const updated = summary?.last_updated
    ? new Date(summary.last_updated).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })
    : null;
  const sourceNames = sources?.data?.map((s) => s.label).join(", ");

  return (
    <header className="hero">
      <div className="wrap">
        <p className="eyebrow">Business listings dashboard</p>
        <h1>
          {total ? (
            <>
              <span className="big">{total.toLocaleString()}</span> businesses across{" "}
              <span className="big">{summary.cities}</span> {summary.cities === 1 ? "city" : "cities"}, what do they tell us?
            </>
          ) : loading ? (
            "Loading the story…"
          ) : (
            "No listings match these filters"
          )}
        </h1>
        {total ? (
          <p className="sub">
            Scraped from {sourceNames}
            {updated ? ` · last update ${updated}` : ""} · {summary.categories} categories ·{" "}
            {pct(summary.with_phone / total)} with a phone number
          </p>
        ) : null}

        {findings.length > 0 && (
          <div className="findings">
            {findings.map((f, i) => (
              <article key={f.kicker} className="finding" style={{ animationDelay: `${i * 80}ms` }}>
                <span className="kicker">{f.kicker}</span>
                <h2>{f.title}</h2>
                <p>{f.text}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}
