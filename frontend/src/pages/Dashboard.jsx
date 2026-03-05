import Header from '../components/Header'
import MetricsCards from '../components/MetricsCards'
import ForecastChart from '../components/ForecastChart'
import RecommendationsPanel from '../components/RecommendationsPanel'
import ExplainabilitySection from '../components/ExplainabilitySection'
import WhatIfControls from '../components/WhatIfControls'
import SustainabilityPanel from '../components/SustainabilityPanel'
import { useDashboard } from '../hooks/useDashboard'

export default function Dashboard() {
    const {
        buildings,
        selectedBuilding,
        setSelectedBuilding,
        forecast,
        recommendations,
        explanation,
        whatIfResult,
        whatIfState,
        handleWhatIfChange,
        metrics,
        loading,
        error,
        weather,
        alerts,
        badges,
        stats,
        carbonImpact
    } = useDashboard()

    return (
        <div className="min-h-screen flex flex-col">
            <Header
                buildings={buildings}
                selectedBuilding={selectedBuilding}
                onBuildingChange={setSelectedBuilding}
            />

            <main className="flex-1 px-4 sm:px-6 py-6 max-w-[1600px] mx-auto w-full">
                {/* Error banner */}
                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
                        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {error} — showing mock data as fallback.
                    </div>
                )}

                {/* Metrics row */}
                <section className="mb-6">
                    <MetricsCards metrics={metrics} />
                </section>

                {/* Main content grid */}
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                    {/* Left column — chart + explainability */}
                    <div className="xl:col-span-2 space-y-6">
                        <ForecastChart forecast={forecast} whatIfResult={whatIfResult} />

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <ExplainabilitySection explanation={explanation} />
                            <SustainabilityPanel
                                weather={weather}
                                alerts={alerts}
                                badges={badges}
                                stats={stats}
                                carbonImpact={carbonImpact}
                            />
                        </div>
                    </div>

                    {/* Right column — recommendations + what-if */}
                    <div className="space-y-6">
                        <WhatIfControls whatIfState={whatIfState} onWhatIfChange={handleWhatIfChange} />
                        <RecommendationsPanel recommendations={recommendations} />
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="text-center text-xs text-ink-faint py-4 border-t border-border-subtle bg-white">
                Urja AI · Campus Energy Optimization System · {new Date().getFullYear()}
            </footer>
        </div>
    )
}
