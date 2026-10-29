import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

export const PALETTE = ["#1f7a8c", "#f2a541", "#bf4342", "#6a994e", "#7b5ea7", "#3d5a80", "#b59f3b", "#8d99ae"];
const OTHER_COLOR = "#c5cad3";
const tooltipStyle = {
  background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 8, color: "var(--ink)", fontSize: 13,
};

// Recharts passes the clicked data differently for Bar vs Pie; normalise to the label.
const labelOf = (d) => d?.label ?? d?.payload?.label ?? d?.payload?.payload?.label;

export function CountBarChart({ data, active, onSelect, horizontal = false }) {
  const height = horizontal ? Math.max(260, data.length * 34) : 300;
  const cells = data.map((d) => (
    <Cell
      key={d.label}
      fill={PALETTE[0]}
      fillOpacity={!active || active === d.label ? 1 : 0.3} // dim everything except the selection
      cursor="pointer"
    />
  ));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout={horizontal ? "vertical" : "horizontal"}
        margin={{ top: 8, right: 16, bottom: 8, left: horizontal ? 24 : 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" vertical={horizontal} horizontal={!horizontal} stroke="var(--line)" />
        {horizontal ? (
          <>
            <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="label" width={110} tick={{ fontSize: 12 }} />
          </>
        ) : (
          <>
            <XAxis dataKey="label" tick={{ fontSize: 12 }} interval={0} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
          </>
        )}
        <Tooltip cursor={{ fill: "rgba(120,130,140,0.12)" }} contentStyle={tooltipStyle} formatter={(v) => [v, "Businesses"]} />
        <Bar dataKey="count" radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]} onClick={(d) => onSelect(labelOf(d))}>
          {cells}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SourcePieChart({ data, active, onSelect }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="label"
          innerRadius={62}
          outerRadius={100}
          paddingAngle={2}
          onClick={(d) => onSelect(labelOf(d))}
        >
          {data.map((d, i) => (
            <Cell
              key={d.label}
              fill={PALETTE[i % PALETTE.length]}
              fillOpacity={!active || active === d.label ? 1 : 0.3}
              cursor="pointer"
            />
          ))}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} formatter={(v, name) => [v, name]} />
        <Legend verticalAlign="bottom" iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  );
}


/** 100%-stacked bars: what each city is made of. Compare the SHAPE of the bars, not their length. */
export function CategoryMixChart({ mix, activeCity, onSelectCity }) {
  const keys = [...mix.categories, "Other"];
  const data = mix.rows.map((r) => ({ city: r.city, ...r.counts, Other: r.other }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(300, data.length * 44 + 70)}>
      <BarChart data={data} layout="vertical" stackOffset="expand" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)" />
        <XAxis type="number" tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="city" width={92} tick={{ fontSize: 12 }} />
        <Tooltip
          cursor={{ fill: "rgba(120,130,140,0.12)" }}
          contentStyle={tooltipStyle}
          formatter={(v, name, item) => {
            const total = item.payload ? keys.reduce((s, k) => s + (item.payload[k] ?? 0), 0) : 0;
            return [`${v} (${total ? Math.round((v / total) * 100) : 0}%)`, name];
          }}
        />
        <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={{ fontSize: 12 }} />
        {keys.map((k, i) => (
          <Bar
            key={k}
            dataKey={k}
            stackId="mix"
            fill={k === "Other" ? OTHER_COLOR : PALETTE[i % PALETTE.length]}
            cursor="pointer"
            onClick={(d) => onSelectCity(d?.payload?.city ?? d?.city)}
          >
            {data.map((row) => (
              <Cell key={row.city} fillOpacity={!activeCity || activeCity === row.city ? 1 : 0.3} />
            ))}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Share of listings that have an address / a phone number, per city. */
export function CompletenessChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--line)" />
        <XAxis dataKey="city" tick={{ fontSize: 12 }} interval={0} />
        <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 12 }} />
        <Tooltip cursor={{ fill: "rgba(120,130,140,0.12)" }} contentStyle={tooltipStyle} formatter={(v, name) => [`${v}%`, name]} />
        <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="address_pct" name="Has address" fill={PALETTE[0]} radius={[4, 4, 0, 0]} />
        <Bar dataKey="phone_pct" name="Has phone" fill={PALETTE[1]} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
