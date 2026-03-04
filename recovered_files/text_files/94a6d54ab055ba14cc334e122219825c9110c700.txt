export default function Header({ buildings, selectedBuilding, onBuildingChange }) {
    const now = new Date()
    const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    const dateStr = now.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })

    return (
        <header className="relative" style={{ background: 'linear-gradient(135deg, #14532d 0%, #166534 40%, #15803d 100%)' }}>
            {/* Shimmering gradient top line */}
            <div className="gradient-line w-full opacity-60" />

            <div className="px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                {/* Logo + wordmark */}
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center shadow-lg">
                        <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white leading-tight tracking-tight">Urja AI</h1>
                        <p className="text-xs text-green-200">Campus Energy Optimization</p>
                    </div>
                </div>

                {/* Building selector */}
                <div className="flex items-center gap-3">
                    <label htmlFor="building-select" className="text-xs text-green-200 whitespace-nowrap hidden sm:block font-medium">
                        Building
                    </label>
                    <select
                        id="building-select"
                        value={selectedBuilding}
                        onChange={e => onBuildingChange(e.target.value)}
                        className="bg-white/15 border border-white/30 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white/40 transition-all cursor-pointer backdrop-blur-sm"
                        style={{ color: 'white' }}
                    >
                        {buildings.map(b => (
                            <option key={b} value={b} style={{ color: '#1a2e1e', background: '#fff' }}>
                                {b.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Date-time badge */}
                <div className="text-right hidden md:block">
                    <p className="text-sm font-semibold text-white">{timeStr}</p>
                    <p className="text-xs text-green-200">{dateStr}</p>
                </div>
            </div>

            {/* Bottom wavy green border */}
            <div className="w-full overflow-hidden leading-none" style={{ height: '20px' }}>
                <svg viewBox="0 0 1200 20" preserveAspectRatio="none" className="w-full h-full">
                    <path d="M0,10 C300,20 600,0 900,10 C1050,15 1150,5 1200,10 L1200,20 L0,20 Z" fill="#ecfdf5" />
                </svg>
            </div>
        </header>
    )
}
