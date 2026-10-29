// Ranked list of business names that occur more than once (chains / multi-branch networks).
export default function RepeatedNames({ data, onSelect }) {
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <ol className="chains">
      {data.map((d, i) => (
        <li key={d.name}>
          <span className="rank">{i + 1}</span>
          <div className="chain-main">
            <div className="chain-top">
              <strong>{d.name}</strong>
              <span className="muted">
                {d.count} listings · {d.cities} {d.cities === 1 ? "city" : "cities"}
              </span>
            </div>
            <div className="track">
              <div className="fill" style={{ width: `${(d.count / max) * 100}%` }} />
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
