import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function RecommendationCard({ rec }) {
    const [expanded, setExpanded] = useState(false)

    const priorityClass = {
        high: 'badge-high',
        medium: 'badge-medium',
        low: 'badge-low',
    }[rec.priority] || 'badge-low'

    return (
        <div className="bg-beige-light border border-border rounded-xl p-4 transition-all duration-200 hover:border-primary-light hover:shadow-sm">
            <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-ink font-medium leading-snug flex-1">{rec.action}</p>
                <span className={priorityClass}>{rec.priority}</span>
            </div>

            <div className="flex items-center gap-3 mt-3">
                <span className="badge-savings">↓ {rec.savings_kwh} kWh</span>
                <span className="text-xs text-ink-muted">≈ ₹{rec.savings_cost_inr.toFixed(0)}</span>

                <button
                    onClick={() => setExpanded(v => !v)}
                    className="ml-auto text-xs text-primary-dark hover:text-primary transition-colors flex items-center gap-1 font-medium"
                >
                    Why?
                    <svg
                        className={`w-3 h-3 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                </button>
            </div>

            <div className={`overflow-hidden transition-all duration-300 ${expanded ? 'max-h-40 mt-3' : 'max-h-0'}`}>
                <p className="text-xs text-ink-soft bg-white rounded-lg px-3 py-2 border border-border-subtle leading-relaxed">
                    {rec.reason}
                </p>
            </div>
        </div>
    )
}

export default function RecommendationsPanel({ recommendations, buildingId }) {
    const navigate = useNavigate()

    if (!recommendations) {
        return (
            <div className="card p-6 space-y-3">
                <p className="section-title">Recommendations</p>
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-20 bg-beige/60 rounded-xl animate-pulse" />
                ))}
            </div>
        )
    }

    return (
        <div className="card p-6 flex flex-col">
            <div className="flex items-center justify-between mb-4">
                <p className="section-title mb-0">Recommendations</p>
                <span className="text-xs text-ink-muted">{recommendations.recommendations.length} actions</span>
            </div>

            <div className="space-y-3 overflow-y-auto max-h-[420px] pr-1 flex-1">
                {recommendations.recommendations.map((rec, i) => (
                    <RecommendationCard key={i} rec={rec} />
                ))}
            </div>

            <div className="mt-6 pt-4 border-t border-border flex items-center justify-between flex-wrap gap-2">
                <p className="text-xs text-ink-muted">Want more detailed AI analysis?</p>
                <div className="flex gap-2">
                    <button
                        onClick={() => navigate(`/deep-recommendations/${buildingId}`)}
                        className="btn-primary py-1.5 px-3 text-xs flex items-center gap-1.5"
                    >
                        Wanna check deeper?
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                    </button>
                    <button
                        onClick={() => navigate(`/enhanced-recommendations/${buildingId}`)}
                        className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5 bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
                    >
                        ✨ Smart Recs
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    )
}
