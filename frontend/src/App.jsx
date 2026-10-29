import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import Hero from "./components/Hero";
import Chapter from "./components/Chapter";
import ChartCard from "./components/ChartCard";
import RepeatedNames from "./components/RepeatedNames";
import ListingsTable from "./components/ListingsTable";
import { CategoryMixChart, CompletenessChart, CountBarChart, SourcePieChart } from "./components/Charts";
import { buildFindings, citiesAreEven, completenessSummary, mostDistinctiveCity, pct } from "./insights";

const EMPTY = { city: "", category: "", source: "" };

export default function App() {
  // `filters` is the single source of truth. Clicking a bar/slice sets one;
  // every chart, the headline findings and the table re-query the API with it.
  const [filters, setFilters] = useState(EMPTY);
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false; // ignore out-of-order responses
    setLoading(true);
    Promise.all([
      api.summary(filters), api.cities(filters), api.categories(filters), api.sources(filters), api.insights(filters),
    ])
      .then(([summary, cities, categories, sources, insights]) => {
        if (cancelled) return;
        setData({ summary, cities, categories, sources, insights });
        setError(null);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [filters]);

  // Click once to filter, click the same item again to clear it.
  const toggle = (key) => (value) =>
    value && setFilters((f) => ({ ...f, [key]: f[key] === value ? "" : value }));

  const { summary, cities, categories, sources, insights } = data;
  const activeFilters = Object.entries(filters).filter(([, v]) => v);
  const first = !summary; // first load: nothing to show yet

  const story = useMemo(() => {
    if (!summary || !insights) return null;
    const distinct = mostDistinctiveCity(insights.category_mix);
    const comp = completenessSummary(insights.completeness);
    return {
      findings: buildFindings({ summary, categories, insights }),
      even: citiesAreEven(cities),
      distinct,
      comp,
      chains: insights.repeated_names,
    };
  }, [summary, categories, cities, insights]);

  return (
    <>
      <Hero summary={summary} sources={sources} findings={story?.findings ?? []} loading={first} />

      <main className="wrap page">
        {error && (
          <div className="banner error" role="alert">
            Could not load data ({error}). Check that the API is running on port 8000.
          </div>
        )}

        {/* <div className="toolbar" aria-live="polite">
          {activeFilters.length === 0 ? (
            <span className="hint">Tip: click any bar or slice to filter the whole page.</span>
          ) : (
            <>
              <span className="hint">Filtering by</span>
              {activeFilters.map(([k, v]) => (
                <button key={k} className="chip" onClick={() => setFilters((f) => ({ ...f, [k]: "" }))}>
                  {k}: {v} ✕
                </button>
              ))}
              <button className="link" onClick={() => setFilters(EMPTY)}>Clear all</button>
            </>
          )}
        </div> */}

        {/* ---------- Chapter 1 ---------- */}
        <Chapter
          number={1}
          title="What we collected"
          lead={
            summary &&
            `${summary.total_listings.toLocaleString()} listings from ${sources?.data.length ?? 0} source${
              sources?.data.length === 1 ? "" : "s"
            }, spread over ${summary.cities} ${summary.cities === 1 ? "city" : "cities"}.`
          }
        >
          <div className="grid g-3-2">
            <ChartCard
              title="Listings per city"
              subtitle={cities && `Top ${cities.data.length} of ${cities.total_groups} · click a bar to filter`}
              note={
                story?.even
                  ? "These bars are almost equal on purpose: collection was capped at a fixed number of listings per city. Compare what each city is made of (chapter 2), not how big it is."
                  : null
              }
              loading={first}
              empty={cities?.data.length === 0}
            >
              {cities && <CountBarChart data={cities.data} active={filters.city} onSelect={toggle("city")} />}
            </ChartCard>
            <ChartCard
              title="Where the data came from"
              subtitle="Click a slice to filter"
              loading={first}
              empty={sources?.data.length === 0}
            >
              {sources && <SourcePieChart data={sources.data} active={filters.source} onSelect={toggle("source")} />}
            </ChartCard>
          </div>
        </Chapter>

        {/* ---------- Chapter 2 ---------- */}
        <Chapter
          number={2}
          title="What kind of businesses are they?"
          lead={
            story?.distinct
              ? `${story.distinct.city} stands out: ${pct(story.distinct.share)} of its listings are ${story.distinct.category.toLowerCase()}, versus ${pct(story.distinct.overall)} across all cities.`
              : categories?.data[0] && summary
              ? `${categories.data[0].label} leads with ${pct(categories.data[0].count / summary.total_listings)} of listings.`
              : null
          }
        >
          <div className="grid">
            <ChartCard
              title="Top categories"
              subtitle={categories && `Top ${categories.data.length} of ${categories.total_groups} · click a bar to filter`}
              loading={first}
              empty={categories?.data.length === 0}
            >
              {categories && (
                <CountBarChart horizontal data={categories.data} active={filters.category} onSelect={toggle("category")} />
              )}
            </ChartCard>
            <ChartCard
              title="What each city is made of"
              subtitle="Share of each city's listings by category · click a bar to filter by city"
              note={
                insights?.category_mix.rows.length === 1
                  ? "Only one city is selected - clear the city filter to compare cities."
                  : null
              }
              loading={first}
              empty={!insights || insights.category_mix.rows.length === 0}
            >
              {insights && (
                <CategoryMixChart mix={insights.category_mix} activeCity={filters.city} onSelectCity={toggle("city")} />
              )}
            </ChartCard>
          </div>
        </Chapter>

        {/* ---------- Chapter 3 ---------- */}
        <Chapter
          number={3}
          title="Who shows up again and again"
          lead={
            story?.chains.length
              ? `${story.chains[0].name} is the most repeated name (${story.chains[0].count} listings). Repeated names point to chains and multi-branch networks.`
              : "No business name appears more than once in this selection."
          }
        >
          {story?.chains.length > 0 && (
            <ChartCard title="Most repeated business names" subtitle="Same name, different locations">
              <RepeatedNames data={story.chains} />
            </ChartCard>
          )}
        </Chapter>

        {/* ---------- Chapter 4 ---------- */}
        <Chapter
          number={4}
          title="How complete is the data?"
          lead={
            story?.comp &&
            `${pct(story.comp.addr)} of listings have an address but only ${pct(story.comp.phone)} have a phone number.${
              story.comp.best.city !== story.comp.worst.city
                ? ` Phone coverage is best in ${story.comp.best.city} (${Math.round(story.comp.best.phone_pct)}%) and weakest in ${story.comp.worst.city} (${Math.round(story.comp.worst.phone_pct)}%).`
                : ""
            }`
          }
        >
          <ChartCard
            title="Address and phone coverage by city"
            subtitle="Share of listings with each field filled in"
            note="OpenStreetMap is volunteer-edited, so coverage depends on how well each city has been mapped. Phone is optional in this project's schema."
            loading={first}
            empty={!insights || insights.completeness.length === 0}
          >
            {insights && <CompletenessChart data={insights.completeness} />}
          </ChartCard>
        </Chapter>

        <Chapter number={5} title="Explore the raw listings" lead="Search by name or address. Filters above also apply here.">
          <ListingsTable filters={filters} />
        </Chapter>

        <footer className="foot">
          Data © OpenStreetMap contributors (ODbL). Counts describe the collected sample, not every business in these
          cities. Sample-data rows, if any, are generated and labelled as such.
        </footer>
      </main>
    </>
  );
}
