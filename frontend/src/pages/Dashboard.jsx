import { useState } from 'react'
import Header from '../components/Header'
import MetricsCards from '../components/MetricsCards'
import ForecastChart from '../components/ForecastChart'
import RecommendationsPanel from '../components/RecommendationsPanel'
import ExplainabilitySection from '../components/ExplainabilitySection'
import WhatIfControls from '../components/WhatIfControls'
import SustainabilityPanel from '../components/SustainabilityPanel'
import AnomalyAlertPanel from '../components/AnomalyAlertPanel'
import CampusBlueprint from '../components/CampusBlueprint'
import BuildingSelector from '../components/BuildingSelector'
import { useDashboard } from '../hooks/useDashboard'

/* Map from campus-blueprint room IDs → backend building IDs */
const ROOM_TO_BUILDING = {
    'lecture-hall-a': 'engineering_block',
    'lecture-hall-b': 'hostel_a',
    'computer-lab': 'hostel_b',
    'library': 'main_library',
    'admin-office': 'admin_block',
    'cafeteria': 'cafeteria',
    'server-room': 'sports_complex',
    'common-area': 'main_library',
}

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState('overview')
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

    /* When user clicks a room on the campus map, sync the backend building */
    function handleMapRoomSelect(roomId) {
        const backendId = ROOM_TO_BUILDING[roomId]
        if (backendId) setSelectedBuilding(backendId)
    }

    /* Friendly display name for current building */
    const buildingDisplayName = selectedBuilding
        ?.replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase()) ?? ''

    return (
        <div className="min-h-screen flex flex-col">
            <Header />

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

                {/* Tabs */}
                <div className="mb-6 border-b border-border-default">
                    <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                        {[
                            { id: 'overview', name: 'Overview' },
                            { id: 'simulations', name: 'Simulations & AI' },
                            { id: 'sustainability', name: 'Sustainability & Actions' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                                    ${activeTab === tab.id
                                        ? 'border-brand-primary text-brand-primary'
                                        : 'border-transparent text-ink-lighter hover:text-ink-base hover:border-border-default'}
                                `}
                            >
                                {tab.name}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* ═══════ OVERVIEW ═══════ */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* Interactive Campus Blueprint — clicking a room syncs the forecast */}
                        <CampusBlueprint onBuildingSelect={handleMapRoomSelect} />

                        {/* 24-Hour Forecast — now above anomalies, synced with map */}
                        <ForecastChart
                            forecast={forecast}
                            whatIfResult={whatIfResult}
                            buildingName={buildingDisplayName}
                        />

                        <AnomalyAlertPanel />
                    </div>
                )}

                {/* ═══════ SIMULATIONS & AI ═══════ */}
                {activeTab === 'simulations' && (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                        <div className="xl:col-span-2 space-y-6">
                            <ForecastChart
                                forecast={forecast}
                                whatIfResult={whatIfResult}
                                buildingName={buildingDisplayName}
                            />
                            <ExplainabilitySection explanation={explanation} />
                        </div>
                        <div className="space-y-6">
                            {/* Building selector — replaces header dropdown */}
                            <BuildingSelector
                                buildings={buildings}
                                selectedBuilding={selectedBuilding}
                                onBuildingChange={setSelectedBuilding}
                            />
                            <WhatIfControls whatIfState={whatIfState} onWhatIfChange={handleWhatIfChange} />
                        </div>
                    </div>
                )}

                {/* ═══════ SUSTAINABILITY ═══════ */}
                {activeTab === 'sustainability' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <RecommendationsPanel recommendations={recommendations} buildingId={selectedBuilding} />
                        <SustainabilityPanel
                            weather={weather}
                            alerts={alerts}
                            badges={badges}
                            stats={stats}
                            carbonImpact={carbonImpact}
                        />
                    </div>
                )}
            </main>

            <footer className="text-center text-xs text-ink-faint py-4 border-t border-border-subtle bg-white">
                Urja AI · Campus Energy Optimization System · {new Date().getFullYear()}
            </footer>
        </div>
    )
}
