import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'

function FeatureTooltip({ active, payload }) {
    if (!active || !payload?.length) return null
    const d = payload[0]
    return (
        <div className="bg-white border border-border rounded-lg p-2.5 text-xs shadow-lg">
            <p className="text-ink-soft">{d.payload.feature}</p>
            <p className="font-semibold" style={{ color: d.fill }}>
                {d.value > 0 ? '+' : ''}{(d.value * 100).toFixed(1)}%
            </p>
        </div>
    )
}

export default function ExplainabilitySection({ explanation }) {
    if (!explanation) {
        return <div className="card p-6 h-64 animate-pulse bg-beige/50" />
    }

    const sorted = [...explanation.feature_contributions].sort((a, b) =>
        Math.abs(b.contribution) - Math.abs(a.contribution)
    )

    return (
        <div className="card p-6">
            <p className="section-title">Why This Forecast?</p>

            {/* Natural-language explanation */}
            <div className="bg-primary-xlight border border-primary-light rounded-xl p-4 mb-5">
                <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary-dark/10 border border-primary-light flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg className="w-3.5 h-3.5 text-primary-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <p className="text-sm text-ink-soft leading-relaxed">{explanation.explanation_text}</p>
                </div>
            </div>

            {/* SHAP bar chart */}
            <p className="text-xs text-ink-muted mb-3">Feature contributions to this forecast</p>
            <ResponsiveContainer width="100%" height={180}>
                <BarChart
                    data={sorted}
                    layout="vertical"
                    margin={{ top: 0, right: 30, left: 80, bottom: 0 }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e8f5ea" horizontal={false} />
                    <XAxis
                        type="number"
                        tick={{ fill: '#9cb89e', fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                    />
                    <YAxis
                        type="category"
                        dataKey="feature"
                        tick={{ fill: '#6b8f6e', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={80}
                    />
                    <Tooltip content={<FeatureTooltip />} cursor={{ fill: 'rgba(34,197,94,0.05)' }} />
                    <ReferenceLine x={0} stroke="#c8e6cc" />
                    <Bar dataKey="contribution" radius={[0, 4, 4, 0]} maxBarSize={14}>
                        {sorted.map((entry, i) => (
                            <Cell
                                key={i}
                                fill={entry.contribution >= 0 ? '#16a34a' : '#d97706'}
                                fillOpacity={0.8}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
            <p className="text-xs text-ink-faint mt-2 text-center">Green = increases consumption · Amber = decreases consumption</p>
        </div>
    )
}
