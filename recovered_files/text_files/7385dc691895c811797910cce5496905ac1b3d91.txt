function StatCard({ icon, label, value, unit, colorClass, trend }) {
    return (
        <div className={`metric-card ${colorClass}`}>
            <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">{label}</span>
                <div className="w-8 h-8 rounded-lg bg-white/70 border border-border flex items-center justify-center">
                    {icon}
                </div>
            </div>
            <div className="flex items-end gap-1.5 mt-1">
                <span className="text-3xl font-bold text-ink tabular-nums">{value}</span>
                <span className="text-sm mb-1 text-ink-muted">{unit}</span>
            </div>
            {trend && <p className="text-xs text-ink-faint mt-0.5">{trend}</p>}
        </div>
    )
}

export default function MetricsCards({ metrics }) {
    if (!metrics) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => (
                    <div key={i} className="metric-card h-28 bg-beige/60 animate-pulse" />
                ))}
            </div>
        )
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
                colorClass="bg-gradient-to-br from-green-500 to-green-600 border-green-400 text-white shadow-lg shadow-green-500/30"
                label="Peak Demand"
                value={metrics.peakKw}
                unit="kW"
                trend="Last 24 hours"
                icon={
                    <svg className="w-4 h-4 text-primary-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                }
            />
            <StatCard
                colorClass="bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200"
                label="Total Consumption"
                value={metrics.totalKwh}
                unit="kWh"
                trend="Forecast period"
                icon={
                    <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                }
            />
            <StatCard
                colorClass="bg-gradient-to-br from-green-100 to-emerald-50 border-green-300"
                label="Potential Savings"
                value={metrics.savedKwh}
                unit="kWh"
                trend="Via recommendations"
                icon={
                    <svg className="w-4 h-4 text-primary-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                }
            />
        </div>
    )
}
