import {
    ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

function formatHour(ts) {
    // Backend may send "2025-07-31T23:00:00+00:00Z" — strip trailing Z if offset exists
    const cleaned = typeof ts === 'string' ? ts.replace(/([+-]\d{2}:\d{2})Z$/, '$1') : ts
    const d = new Date(cleaned)
    if (isNaN(d)) return ts  // fallback: show raw string
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null
    // Filter out the confidence band (array value, not renderable as a number)
    const visible = payload.filter(e => !Array.isArray(e.value))
    if (!visible.length) return null
    return (
        <div className="bg-white border border-border rounded-xl p-3 text-xs shadow-xl">
            <p className="text-ink-muted mb-2 font-medium">{label}</p>
            {visible.map((entry, i) => (
                <div key={i} className="flex items-center gap-2 mb-1">
                    <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
                    <span className="text-ink-soft capitalize">{entry.name}:</span>
                    <span className="font-semibold text-ink">{Number(entry.value).toFixed(1)} kWh</span>
                </div>
            ))}
        </div>
    )
}


export default function ForecastChart({ forecast, whatIfResult }) {
    if (!forecast) {
        return <div className="card p-6 h-72 animate-pulse bg-beige/50" />
    }

    const basePoints = forecast.forecast
    const modPoints = whatIfResult?.modified_forecast || []

    const data = basePoints.map((p, i) => ({
        time: formatHour(p.timestamp),
        Forecast: p.consumption,
        'Confidence Band': [p.lower_bound, p.upper_bound],
        ...(modPoints[i] ? { 'What-If': modPoints[i].consumption } : {}),
    }))

    return (
        <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
                <p className="section-title mb-0">24-Hour Forecast</p>
                {whatIfResult && (
                    <p className="text-xs text-primary-dark bg-primary-xlight border border-primary-light rounded-full px-3 py-1 font-medium">
                        What-If active
                    </p>
                )}
            </div>

            <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={data} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
                    <defs>
                        <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.18} />
                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0.02} />
                        </linearGradient>
                    </defs>

                    <CartesianGrid strokeDasharray="3 3" stroke="#e8f5ea" vertical={false} />

                    <XAxis
                        dataKey="time"
                        tick={{ fill: '#9cb89e', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        interval={3}
                    />
                    <YAxis
                        tick={{ fill: '#9cb89e', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        unit=" kWh"
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '12px', color: '#6b8f6e' }} />

                    <Area
                        type="monotone"
                        dataKey="Confidence Band"
                        fill="url(#ciGrad)"
                        stroke="#22c55e"
                        strokeWidth={0}
                        strokeOpacity={0.3}
                        name="Confidence Band"
                    />
                    <Line
                        type="monotone"
                        dataKey="Forecast"
                        stroke="#16a34a"
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 5, fill: '#16a34a', strokeWidth: 0 }}
                    />
                    {whatIfResult && (
                        <Line
                            type="monotone"
                            dataKey="What-If"
                            stroke="#d97706"
                            strokeWidth={2}
                            strokeDasharray="5 3"
                            dot={false}
                            activeDot={{ r: 5, fill: '#d97706', strokeWidth: 0 }}
                        />
                    )}
                </ComposedChart>
            </ResponsiveContainer>

            {whatIfResult && (
                <p className="mt-3 text-xs text-ink-muted bg-beige rounded-lg px-4 py-2 border border-border">
                    {whatIfResult.delta_summary}
                </p>
            )}
        </div>
    )
}
