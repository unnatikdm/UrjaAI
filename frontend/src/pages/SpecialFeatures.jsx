import { useState } from 'react'
import Header from '../components/Header'
import Browniepoint1 from '../components/Browniepoint1'

export default function SpecialFeatures() {
    const [activeTab, setActiveTab] = useState('browniepoint1')
    const [buildings] = useState(['Admin Block', 'Engineering Block'])
    const [selectedBuilding, setSelectedBuilding] = useState('Admin Block')

    return (
        <div className="min-h-screen flex flex-col bg-white">
            <Header
                buildings={buildings}
                selectedBuilding={selectedBuilding}
                onBuildingChange={setSelectedBuilding}
            />

            <main className="flex-1 px-4 sm:px-6 py-6 max-w-[1600px] mx-auto w-full">
                {/* Page Title */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-ink-default mb-2">🎉 Special Features</h1>
                    <p className="text-ink-default text-lg">Advanced ML Models & Energy Intelligence Systems</p>
                </div>

                {/* Tab Navigation */}
                <div className="mb-8 border-b border-border-subtle">
                    <div className="flex gap-8">
                        <button
                            onClick={() => setActiveTab('browniepoint1')}
                            className={`pb-4 px-2 font-semibold text-lg relative transition-colors ${activeTab === 'browniepoint1'
                                    ? 'text-emerald-600'
                                    : 'text-ink-faint hover:text-ink-default'
                                }`}
                        >
                            🌱 Carbon Tracker
                            {activeTab === 'browniepoint1' && (
                                <div className="absolute bottom-0 left-0 right-0 h-1 bg-emerald-600 rounded-full"></div>
                            )}
                        </button>
                    </div>
                </div>

                {/* Tab Content */}
                <div className="animate-fadeIn">
                    {activeTab === 'browniepoint1' && (
                        <Browniepoint1 selectedBuilding={selectedBuilding} />
                    )}
                </div>
            </main>

            {/* Footer */}
            <footer className="text-center text-xs text-ink-faint py-4 border-t border-border-subtle bg-white">
                Urja AI · Campus Energy Optimization System · {new Date().getFullYear()}
            </footer>
        </div>
    )
}
