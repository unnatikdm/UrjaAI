import { useState, useEffect, useCallback, useRef } from 'react'
import {
    getBuildings,
    getForecast,
    getRecommendations,
    getExplanation,
    postWhatIf,
} from '../services/api'

const DEBOUNCE_MS = 350

export function useDashboard() {
    const [buildings, setBuildings] = useState([])
    const [selectedBuilding, setSelectedBuilding] = useState('main_library')

    const [forecast, setForecast] = useState(null)
    const [recommendations, setRecommendations] = useState(null)
    const [explanation, setExplanation] = useState(null)
    const [whatIfResult, setWhatIfResult] = useState(null)

    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const [whatIfState, setWhatIfState] = useState({
        temperature_offset: 0,
        occupancy_multiplier: 1,
    })

    const debounceTimer = useRef(null)

    // Sustainability State
    const [weather, setWeather] = useState(null)
    const [alerts, setAlerts] = useState(null)
    const [badges, setBadges] = useState(null)
    const [stats, setStats] = useState(null)
    const [carbonImpact, setCarbonImpact] = useState(null)

    // Load buildings list and static sustainability data once
    useEffect(() => {
        getBuildings().then(setBuildings).catch(console.error)

        // Fetch static sustainability data
        Promise.all([
            import('../services/api').then(m => m.getWeather()),
            import('../services/api').then(m => m.getWeatherAlerts()),
            import('../services/api').then(m => m.getBadges()),
            import('../services/api').then(m => m.getStats())
        ]).then(([w, a, b, s]) => {
            setWeather(w)
            setAlerts(a)
            setBadges(b)
            setStats(s)
        }).catch(err => console.error("Could not load sustainability data:", err))

    }, [])

    // Load main data whenever selected building changes
    useEffect(() => {
        async function load() {
            setLoading(true)
            setError(null)
            try {
                const [fc, recs, exp] = await Promise.all([
                    getForecast(selectedBuilding),
                    getRecommendations(selectedBuilding, whatIfState),
                    getExplanation(selectedBuilding),
                ])
                setForecast(fc)
                setRecommendations(recs)
                setExplanation(exp)
                setWhatIfResult(null) // reset what-if on building change

                // Calculate baseline carbon impact based on recommendations
                if (recs && recs.recommendations) {
                    const savedKwh = recs.recommendations.reduce((s, r) => s + r.savings_kwh, 0);
                    const { postCarbonImpact } = await import('../services/api');
                    const impact = await postCarbonImpact(savedKwh);
                    setCarbonImpact(impact);
                }

            } catch (e) {
                setError(e.message || 'Failed to load data')
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [selectedBuilding])

    // Debounced what-if re-fetch
    const handleWhatIfChange = useCallback((key, value) => {
        setWhatIfState(prev => {
            const next = { ...prev, [key]: value }

            if (debounceTimer.current) clearTimeout(debounceTimer.current)
            debounceTimer.current = setTimeout(async () => {
                try {
                    const [result, recs] = await Promise.all([
                        postWhatIf(selectedBuilding, next),
                        getRecommendations(selectedBuilding, next)
                    ])
                    setWhatIfResult(result)
                    setRecommendations(recs)

                    // Update carbon impact based on new recommendations
                    if (recs && recs.recommendations) {
                        const savedKwh = recs.recommendations.reduce((s, r) => s + r.savings_kwh, 0);
                        const { postCarbonImpact } = await import('../services/api');
                        const impact = await postCarbonImpact(savedKwh);
                        setCarbonImpact(impact);
                    }
                } catch (e) {
                    console.error('What-if fetch failed', e)
                }
            }, DEBOUNCE_MS)

            return next
        })
    }, [selectedBuilding])

    // Derived metrics
    const metrics = forecast
        ? {
            peakKw: Math.max(...forecast.forecast.map(p => p.consumption)).toFixed(1),
            totalKwh: forecast.forecast.reduce((s, p) => s + p.consumption, 0).toFixed(1),
            savedKwh: recommendations
                ? recommendations.recommendations.reduce((s, r) => s + r.savings_kwh, 0).toFixed(1)
                : '—',
        }
        : null

    return {
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
    }
}
