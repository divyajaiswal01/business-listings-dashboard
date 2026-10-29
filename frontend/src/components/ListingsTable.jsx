import { useEffect, useState } from "react";
import { api } from "../api";

const PAGE_SIZE = 10;

export default function ListingsTable({ filters }) {
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Wait 350ms after typing stops before calling the API.
  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  // Any filter / search change goes back to page 1.
  useEffect(() => setPage(1), [filters, debounced]);

  useEffect(() => {
    let cancelled = false; // ignore out-of-order responses
    setLoading(true);
    api
      .listings(filters, page, debounced, PAGE_SIZE)
      .then((d) => !cancelled && (setData(d), setError(null)))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [filters, page, debounced]);

  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <section className="card">
      <header className="card-head row">
        <div>
          <h3>Listings</h3>
          <p>{data.total.toLocaleString()} businesses</p>
        </div>
        <input
          className="search"
          type="search"
          placeholder="Search name or address"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search listings"
        />
      </header>
      {error ? (
        <div className="placeholder error">{error}</div>
      ) : (
        <div className="table-wrap" style={{ opacity: loading ? 0.6 : 1 }}>
          <table>
            <thead>
              <tr>
                <th>Business</th><th>Category</th><th>City</th><th>Address</th><th>Phone</th><th>Source</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id}>
                  <td className="strong">{r.business_name}</td>
                  <td>{r.category}</td>
                  <td>{r.city}</td>
                  <td className="muted">{r.address ?? "–"}</td>
                  <td>{r.phone ?? "–"}</td>
                  <td>{r.source}</td>
                </tr>
              ))}
              {!loading && data.items.length === 0 && (
                <tr><td colSpan={6} className="placeholder">No listings found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <footer className="pager">
        <button onClick={() => setPage((p) => p - 1)} disabled={page <= 1}>Previous</button>
        <span>Page {page} of {pages}</span>
        <button onClick={() => setPage((p) => p + 1)} disabled={page >= pages}>Next</button>
      </footer>
    </section>
  );
}
