function Slider({ id, label, min, max, step, value, onChange, format }) {
    const pct = ((value - min) / (max - min)) * 100

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <label htmlFor={id} className="text-sm text-ink-soft font-medium">{label}</label>
                <span className="text-sm font-semibold text-primary-dark tabular-nums">{format(value)}</span>
            </div>
            <input
                id={id}
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={e => onChange(parseFloat(e.target.value))}
                style={{ '--val': `${pct}%` }}
                className="w-full"
            />
            <div className="flex justify-between text-xs text-ink-faint">
                <span>{format(min)}</span>
                <span>{format(max)}</span>
            </div>
        </div>
    )
}

export default function WhatIfControls({ whatIfState, onWhatIfChange }) {
    const isActive =
        whatIfState.temperature_offset !== 0 || whatIfState.occupancy_multiplier !== 1

    return (
        <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
                <div>
                    <p className="section-title mb-0.5">What-If Simulator</p>
                    <p className="text-xs text-ink-faint">Adjust parameters to explore scenarios</p>
                </div>
                {isActive && (
                    <button
                        onClick={() => {
                            onWhatIfChange('temperature_offset', 0)
                            onWhatIfChange('occupancy_multiplier', 1)
                        }}
                        className="text-xs text-ink-muted hover:text-ink border border-border hover:border-border-strong rounded-lg px-3 py-1.5 transition-colors"
                    >
                        Reset
                    </button>
                )}
            </div>

            <div className="space-y-6">
                <Slider
                    id="temp-offset"
                    label="Temperature Offset"
                    min={-5}
                    max={5}
                    step={0.5}
                    value={whatIfState.temperature_offset}
                    onChange={v => onWhatIfChange('temperature_offset', v)}
                    format={v => `${v > 0 ? '+' : ''}${v.toFixed(1)} °C`}
                />

                <Slider
                    id="occ-multiplier"
                    label="Occupancy Multiplier"
                    min={0.5}
                    max={1.5}
                    step={0.05}
                    value={whatIfState.occupancy_multiplier}
                    onChange={v => onWhatIfChange('occupancy_multiplier', v)}
                    format={v => `${v.toFixed(2)}×`}
                />
            </div>

            {isActive && (
                <div className="mt-4 flex items-center gap-2 text-xs text-primary-dark bg-primary-xlight border border-primary-light rounded-lg px-3 py-2">
                    <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Scenario active — chart updated
                </div>
            )}
        </div>
    )
}
