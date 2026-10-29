// Turns raw API numbers into sentences. Every claim is computed from the data on screen,
// nothing is hard-coded, so the story changes when the filters change.

export const pct = (x) => `${Math.round(x * 100)}%`;
const lower = (s) => s.toLowerCase();
const joinNames = (names) =>
  names.length <= 1 ? names.join("") : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;

/** Is the per-city bar chart "flat"? (happens when collection used a fixed cap per city) */
export function citiesAreEven(cities) {
  const counts = (cities?.data ?? []).map((d) => d.count);
  if (counts.length < 3) return false;
  return Math.max(...counts) / Math.max(1, Math.min(...counts)) < 1.35;
}

/** The city whose mix differs most from the overall mix ("lift" = city share / overall share). */
export function mostDistinctiveCity(mix) {
  if (!mix || mix.rows.length < 2) return null;
  const grand = mix.rows.reduce((s, r) => s + r.total, 0);
  let best = null;
  for (const cat of mix.categories) {
    const overall = mix.rows.reduce((s, r) => s + (r.counts[cat] ?? 0), 0) / grand;
    if (overall === 0) continue;
    for (const r of mix.rows) {
      const n = r.counts[cat] ?? 0;
      const share = n / r.total;
      const lift = share / overall;
      if (n >= 8 && share >= 0.15 && lift >= 1.4 && (!best || lift > best.lift)) {
        best = { city: r.city, category: cat, share, overall, lift };
      }
    }
  }
  return best;
}

export function completenessSummary(rows) {
  if (!rows?.length) return null;
  const total = rows.reduce((s, r) => s + r.total, 0);
  const addr = rows.reduce((s, r) => s + (r.address_pct * r.total) / 100, 0) / total;
  const phone = rows.reduce((s, r) => s + (r.phone_pct * r.total) / 100, 0) / total;
  const byPhone = [...rows].sort((a, b) => b.phone_pct - a.phone_pct);
  return { addr, phone, best: byPhone[0], worst: byPhone[byPhone.length - 1] };
}

/** Up to four headline findings shown at the top of the page. */
export function buildFindings({ summary, categories, insights }) {
  const out = [];
  const total = summary?.total_listings ?? 0;
  if (!total || !categories?.data?.length) return out;

  const top = categories.data[0];
  const top3 = categories.data.slice(0, 3);
  const top3Share = top3.reduce((s, d) => s + d.count, 0) / total;
  out.push({
    kicker: "Category mix",
    title: `${top.label} is the biggest category (${pct(top.count / total)})`,
    text: `${joinNames(top3.map((d) => d.label))} together make up ${pct(top3Share)} of all listings.`,
  });

  const d = mostDistinctiveCity(insights?.category_mix);
  if (d) {
    out.push({
      kicker: "Local flavour",
      title: `${d.city} leans towards ${lower(d.category)}`,
      text: `${pct(d.share)} of its listings are ${lower(d.category)}, against ${pct(d.overall)} across the top cities.`,
    });
  }

  const chain = insights?.repeated_names?.[0];
  if (chain) {
    out.push({
      kicker: "Repeated names",
      title: `${chain.name} appears ${chain.count} times`,
      text: `It is the most repeated business name, found in ${chain.cities} ${chain.cities === 1 ? "city" : "cities"} - a sign of chains and multi-branch networks.`,
    });
  }

  const c = completenessSummary(insights?.completeness);
  if (c && c.best.city !== c.worst.city) {
    out.push({
      kicker: "Data quality",
      title: `Phone numbers: ${Math.round(c.worst.phone_pct)}% in ${c.worst.city}, ${Math.round(c.best.phone_pct)}% in ${c.best.city}`,
      text: `Only ${pct(c.phone)} of listings have a phone number overall, while ${pct(c.addr)} have an address.`,
    });
  }
  return out.slice(0, 4);
}
