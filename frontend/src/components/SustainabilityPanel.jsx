import React from 'react';

export default function SustainabilityPanel({ weather, alerts, badges, stats, carbonImpact }) {

    // Get current weather (first item in hourly array)
    const currentTemp = weather?.temperature?.[0];
    const currentHumidity = weather?.humidity?.[0];
    const currentWind = weather?.windspeed?.[0];

    // Determine active badge
    const activeBadge = stats?.current_badge || badges?.sapling;

    // Calculate progress to next badge
    let nextBadge = null;
    let progressPercent = 100;

    if (badges && activeBadge) {
        const badgeKeys = ['seedling', 'sapling', 'tree', 'forest', 'carbon_hero'];
        const currentIndex = badgeKeys.indexOf(activeBadge.key);
        if (currentIndex < badgeKeys.length - 1) {
            nextBadge = badges[badgeKeys[currentIndex + 1]];
            const currentObj = badges[activeBadge.key];
            if (nextBadge && currentObj) {
                const range = nextBadge.threshold - currentObj.threshold;
                const currentProgress = stats?.cumulative_co2_saved - currentObj.threshold;
                progressPercent = Math.min(100, Math.max(0, (currentProgress / range) * 100));
            }
        }
    }

    return (
        <div className="bg-white rounded-2xl border border-border-subtle shadow-sm overflow-hidden flex flex-col h-full">
            <div className="px-5 py-4 border-b border-border-subtle bg-gradient-to-r from-emerald-50 to-teal-50 flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-bold text-ink-main flex items-center gap-2">
                        <span>🌱</span> Brownie Points Impact
                    </h2>
                    <p className="text-sm text-emerald-700 font-medium">Carbon Footprint Tracker</p>
                </div>
                {activeBadge && (
                    <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-emerald-100 shadow-sm">
                        <span className="text-xl">{activeBadge.icon}</span>
                        <span className="font-bold text-emerald-800 text-sm">{activeBadge.name} Tier</span>
                    </div>
                )}
            </div>

            <div className="p-5 flex-1 flex flex-col gap-6">

                {/* Weather Highlights */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Live Campus Weather</h3>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-black text-slate-700">{currentTemp !== undefined ? `${currentTemp}°C` : '--'}</span>
                            <span className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                                <span>💧</span> {currentHumidity !== undefined ? `${currentHumidity}%` : '--'}
                            </span>
                            <span className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                                <span>💨</span> {currentWind !== undefined ? `${currentWind} km/h` : '--'}
                            </span>
                        </div>
                    </div>

                    {/* Alerts Section */}
                    {alerts && alerts.length > 0 ? (
                        <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                            <h3 className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                                ⚠️ Weather Alert
                            </h3>
                            <div className="flex flex-col gap-2">
                                {alerts.slice(0, 2).map((alert, i) => (
                                    <p key={i} className="text-sm text-amber-900 font-medium">
                                        <span className="capitalize font-bold">{alert.type.replace('_', ' ')}:</span> {alert.message}
                                    </p>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-100 flex items-center justify-center">
                            <p className="text-sm text-emerald-700 font-medium text-center">🌤️ Optimal conditions for solar generation</p>
                        </div>
                    )}
                </div>

                {/* Gamification Progress */}
                {nextBadge && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm font-medium">
                            <span className="text-slate-500">Progress to {nextBadge.name} {nextBadge.icon}</span>
                            <span className="text-emerald-600 font-bold">{stats?.cumulative_co2_saved?.toFixed(1) || 0} / {nextBadge.threshold} kg CO₂</span>
                        </div>
                        <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                            <div
                                className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${progressPercent}%` }}
                            ></div>
                        </div>
                    </div>
                )}

                {/* Impact Metrics (What-If Interactive) */}
                <div className="mt-2">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Projected Savings Impact</h3>
                    {carbonImpact ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <ImpactCard
                                icon="☁️"
                                value={carbonImpact.co2_saved_kg}
                                unit="kg"
                                label="CO₂ Avoided"
                                color="text-teal-600"
                                bg="bg-teal-50"
                                border="border-teal-100"
                            />
                            <ImpactCard
                                icon="🌳"
                                value={carbonImpact.trees_equivalent}
                                unit="trees"
                                label="Equivalent"
                                color="text-emerald-600"
                                bg="bg-emerald-50"
                                border="border-emerald-100"
                            />
                            <ImpactCard
                                icon="🚗"
                                value={carbonImpact.car_km_avoided}
                                unit="km"
                                label="Car Travel"
                                color="text-indigo-600"
                                bg="bg-indigo-50"
                                border="border-indigo-100"
                            />
                            <ImpactCard
                                icon="📱"
                                value={carbonImpact.smartphone_charges}
                                unit="charges"
                                label="Smartphones"
                                color="text-blue-600"
                                bg="bg-blue-50"
                                border="border-blue-100"
                            />
                        </div>
                    ) : (
                        <div className="text-center py-6 text-sm text-slate-400 border border-dashed border-slate-200 rounded-xl">
                            Adjust "What-If" parameters to see potential carbon savings!
                        </div>
                    )}
                </div>

                {/* Leaderboard Section */}
                <div className="mt-2">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1">🏆 Inter-College Carbon Leaderboard</h3>
                    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                        <div className="divide-y divide-slate-100">
                            {[
                                { rank: 1, name: 'Vidyalankar', score: '3,240', icon: '🥇', highlight: true },
                                { rank: 2, name: 'VJTI', score: '2,890', icon: '🥈', highlight: false },
                                { rank: 3, name: 'SPIT', score: '2,450', icon: '🥉', highlight: false }
                            ].map((college, idx) => (
                                <div key={idx} className={`flex items-center justify-between p-3 ${college.highlight ? 'bg-emerald-50' : 'hover:bg-slate-50'} transition-colors`}>
                                    <div className="flex items-center gap-3">
                                        <span className="text-xl">{college.icon}</span>
                                        <span className={`font-bold ${college.highlight ? 'text-emerald-800' : 'text-slate-700'}`}>{college.name}</span>
                                    </div>
                                    <span className={`text-sm font-semibold ${college.highlight ? 'text-emerald-600' : 'text-slate-500'}`}>{college.score} kg CO₂</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}

function ImpactCard({ icon, value, unit, label, color, bg, border }) {
    return (
        <div className={`${bg} border ${border} rounded-xl p-3 flex flex-col items-center text-center transition-all hover:scale-105`}>
            <span className="text-2xl mb-1">{icon}</span>
            <div className={`font-black text-lg ${color}`}>{value !== undefined ? value : '--'}</div>
            <div className={`text-[10px] font-bold uppercase tracking-wide ${color} opacity-80 mt-1`}>
                {label} ({unit})
            </div>
        </div>
    );
}
