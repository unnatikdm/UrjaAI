/**
 * mockData.js
 * Static mock responses matching the backend API contract.
 * Used as fallback when VITE_API_BASE_URL is not set.
 */

const now = new Date()
const hourlyTimestamps = Array.from({ length: 24 }, (_, i) => {
    const d = new Date(now)
    d.setHours(d.getHours() - 12 + i, 0, 0, 0)
    return d.toISOString()
})

const dailyPattern = [42, 39, 37, 36, 36, 38, 45, 58, 75, 92, 105, 112, 108, 115, 118, 114, 108, 102, 95, 85, 75, 65, 55, 48]

export const MOCK_FORECAST = {
    building_id: 'main_library',
    generated_at: now.toISOString(),
    forecast: hourlyTimestamps.map((ts, i) => {
        const base = dailyPattern[new Date(ts).getHours()]
        return {
            timestamp: ts,
            consumption: parseFloat((base + Math.sin(i) * 3).toFixed(2)),
            lower_bound: parseFloat((base * 0.92).toFixed(2)),
            upper_bound: parseFloat((base * 1.08).toFixed(2)),
        }
    }),
}

export const MOCK_RECOMMENDATIONS = {
    building_id: 'main_library',
    recommendations: [
        {
            action: 'Pre-cool building during off-peak hours (22:00–06:00)',
            savings_kwh: 13.5,
            savings_cost_inr: 101.25,
            priority: 'high',
            reason: 'Shifting cooling load to off-peak tariff bands reduces demand charges and cuts unit cost by ~30%.',
        },
        {
            action: 'Raise HVAC setpoint by 1 °C during 11:00–14:00 peak window',
            savings_kwh: 9.0,
            savings_cost_inr: 67.5,
            priority: 'medium',
            reason: 'Each 1 °C setpoint increase reduces HVAC energy consumption by approximately 6–8%.',
        },
        {
            action: 'Dim non-essential lighting to 60 % in low-occupancy zones',
            savings_kwh: 5.6,
            savings_cost_inr: 42.0,
            priority: 'medium',
            reason: 'Current average occupancy is 38%, well below the 70% threshold. Automated dimming achieves meaningful savings with no comfort impact.',
        },
        {
            action: 'Auto-shutdown idle lab/office equipment after 20 min of inactivity',
            savings_kwh: 4.5,
            savings_cost_inr: 33.75,
            priority: 'low',
            reason: 'Standby power from computers, projectors, and lab instruments typically accounts for 4–7% of total building consumption.',
        },
    ],
}

export const MOCK_EXPLANATION = {
    building_id: 'main_library',
    explanation_text:
        'The forecast for main_library is approximately 15% above the 7-day average, primarily driven by high outdoor temperature and above-normal occupancy levels during peak hours (10:00–15:00).',
    feature_contributions: [
        { feature: 'Temperature', contribution: 0.31 },
        { feature: 'Hour of Day', contribution: 0.24 },
        { feature: 'Occupancy', contribution: 0.20 },
        { feature: 'Day of Week', contribution: 0.12 },
        { feature: 'Humidity', contribution: 0.08 },
        { feature: 'Solar Irradiance', contribution: -0.05 },
    ],
}

export const MOCK_WHATIF = (tempOffset, occMultiplier) => {
    const scaledForecast = MOCK_FORECAST.forecast.map(p => {
        const modified = p.consumption * occMultiplier * (1 + tempOffset * 0.015)
        return {
            ...p,
            consumption: parseFloat(modified.toFixed(2)),
            lower_bound: parseFloat((modified * 0.92).toFixed(2)),
            upper_bound: parseFloat((modified * 1.08).toFixed(2)),
        }
    })
    const baseTotal = MOCK_FORECAST.forecast.reduce((s, p) => s + p.consumption, 0)
    const modTotal = scaledForecast.reduce((s, p) => s + p.consumption, 0)
    const delta = modTotal - baseTotal
    return {
        building_id: 'main_library',
        baseline_forecast: MOCK_FORECAST.forecast,
        modified_forecast: scaledForecast,
        delta_summary: `With a temperature offset of ${tempOffset > 0 ? '+' : ''}${tempOffset.toFixed(1)} °C and occupancy multiplier of ${occMultiplier.toFixed(1)}×, total consumption would ${delta >= 0 ? 'increase' : 'decrease'} by ${Math.abs(delta).toFixed(1)} kWh (${Math.abs((delta / baseTotal) * 100).toFixed(1)}%) over 24 hours.`,
    }
}

export const MOCK_BUILDINGS = [
    'main_library',
    'engineering_block',
    'admin_block',
    'sports_complex',
    'hostel_a',
    'hostel_b',
    'cafeteria',
]
