const STATUS_COLORS = {
    main_library:       'bg-amber-400',
    engineering_block:   'bg-red-400',
    admin_block:         'bg-emerald-400',
    sports_complex:      'bg-rose-400',
    hostel_a:            'bg-emerald-400',
    hostel_b:            'bg-amber-400',
    cafeteria:           'bg-red-400',
}

const ICONS = {
    main_library:       '📚',
    engineering_block:   '🏗️',
    admin_block:         '🏢',
    sports_complex:      '🏟️',
    hostel_a:            '🏠',
    hostel_b:            '🏠',
    cafeteria:           '🍽️',
}

function formatName(id) {
    return id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function BuildingSelector({ buildings, selectedBuilding, onBuildingChange }) {
    if (!buildings?.length) return null

    return (
        <div className="card p-5">
            <div className="mb-4">
                <p className="section-title mb-0.5">Select Building</p>
                <p className="text-xs text-ink-faint">Choose a building to view its forecast & simulations</p>
            </div>

            <div className="space-y-1.5 max-h-[280px] overflow-y-auto pr-1">
                {buildings.map(b => {
                    const isActive = selectedBuilding === b
                    return (
                        <button
                            key={b}
                            onClick={() => onBuildingChange(b)}
                            className={`
                                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all text-sm
                                ${isActive
                                    ? 'bg-green-50 border border-green-200 text-green-800 font-semibold shadow-sm'
                                    : 'hover:bg-surface-sunken border border-transparent text-ink-base'}
                            `}
                        >
                            <span className="text-base">{ICONS[b] || '🏢'}</span>
                            <span className="flex-1">{formatName(b)}</span>
                            <span className={`w-2.5 h-2.5 rounded-full ${STATUS_COLORS[b] || 'bg-gray-300'}`} />
                            {isActive && (
                                <svg className="w-4 h-4 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </button>
                    )
                })}
            </div>
        </div>
    )
}
