import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE_URL = '/api/browniepoint1'

export default function Browniepoint1({ selectedBuilding }) {
    const [weather, setWeather] = useState(null)
    const [carbonImpact, setCarbonImpact] = useState(null)
    const [alerts, setAlerts] = useState([])
    const [badges, setBadges] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [activeSection, setActiveSection] = useState('weather')

    useEffect(() => {
        fetchBrowniepoint1Data()
    }, [selectedBuilding])

    const fetchBrowniepoint1Data = async () => {
        setLoading(true)
        try {
            const [weatherRes, alertsRes, badgesRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/weather`),
                axios.get(`${API_BASE_URL}/weather-alerts`),
                axios.get(`${API_BASE_URL}/badges`)
            ])

            setWeather(weatherRes.data)
            setAlerts(alertsRes.data.alerts || [])
            setBadges(badgesRes.data || [])
            setError(null)
        } catch (err) {
            console.error('Error fetching browniepoint1 data:', err)
            setError('Failed to load energy tracker data')
        } finally {
            setLoading(false)
        }
    }

    const calculateCarbonSavings = async (energySaved) => {
        try {
            const res = await axios.post(`${API_BASE_URL}/carbon-impact`, {
                energy_saved_kwh: energySaved,
                timestamp: new Date().toISOString()
            })
            setCarbonImpact(res.data)
        } catch (err) {
            console.error('Error calculating carbon impact:', err)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
                    <p className="text-ink-default">Loading Carbon Tracker...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Error Banner */}
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {error}
                </div>
            )}

            {/* Section Navigation */}
            <div className="flex gap-2 border-b border-border-subtle">
                {['weather', 'carbon'].map(section => (
                    <button
                        key={section}
                        onClick={() => setActiveSection(section)}
                        className={`pb-3 px-4 font-medium transition-colors capitalize ${activeSection === section
                                ? 'text-emerald-600 border-b-2 border-emerald-600'
                                : 'text-ink-faint hover:text-ink-default'
                            }`}
                    >
                        {section === 'weather' && '🌤️ Weather'}
                        {section === 'carbon' && '🌱 Carbon Impact'}
                    </button>
                ))}
            </div>

            {/* Weather Section */}
            {activeSection === 'weather' && weather && (
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-6 border border-border-subtle">
                    <h2 className="text-2xl font-bold text-ink-default mb-6 flex items-center gap-2">
                        🌤️ Live Weather Forecast
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        {weather.timestamps && weather.timestamps.slice(0, 8).map((time, idx) => (
                            <div key={idx} className="bg-white rounded-lg p-4 border border-border-subtle hover:shadow-md transition-shadow">
                                <p className="text-sm text-ink-faint mb-2">{new Date(time).toLocaleTimeString()}</p>
                                <div className="text-3xl mb-2">
                                    {weather.temperature && weather.temperature[idx] ? `${Math.round(weather.temperature[idx])}°C` : 'N/A'}
                                </div>
                                <div className="text-sm space-y-1 text-ink-default">
                                    <p>💧 Humidity: {weather.humidity?.[idx]}%</p>
                                    <p>☁️ Cloud: {weather.cloudcover?.[idx]}%</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-border-subtle">
                        <h3 className="font-semibold text-ink-default mb-4">📊 Forecast Details</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="p-3 bg-blue-50 rounded-lg">
                                <p className="text-xs text-ink-faint mb-1">Max Temp</p>
                                <p className="text-lg font-bold text-blue-600">
                                    {weather.temperature ? Math.max(...weather.temperature.slice(0, 24))?.toFixed(1) : 'N/A'}°C
                                </p>
                            </div>
                            <div className="p-3 bg-cyan-50 rounded-lg">
                                <p className="text-xs text-ink-faint mb-1">Avg Humidity</p>
                                <p className="text-lg font-bold text-cyan-600">
                                    {weather.humidity ? (weather.humidity.slice(0, 24).reduce((a, b) => a + b, 0) / 24)?.toFixed(0) : 'N/A'}%
                                </p>
                            </div>
                            <div className="p-3 bg-emerald-50 rounded-lg">
                                <p className="text-xs text-ink-faint mb-1">Precipitation</p>
                                <p className="text-lg font-bold text-emerald-600">
                                    {weather.precipitation ? weather.precipitation.slice(0, 24).reduce((a, b) => a + b, 0)?.toFixed(1) : '0'} mm
                                </p>
                            </div>
                            <div className="p-3 bg-orange-50 rounded-lg">
                                <p className="text-xs text-ink-faint mb-1">Avg Wind</p>
                                <p className="text-lg font-bold text-orange-600">
                                    {weather.windspeed ? (weather.windspeed.slice(0, 24).reduce((a, b) => a + b, 0) / 24)?.toFixed(1) : 'N/A'} m/s
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}



            {/* Carbon Impact Section */}
            {activeSection === 'carbon' && (
                <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-6 border border-border-subtle">
                    <h2 className="text-2xl font-bold text-ink-default mb-6 flex items-center gap-2">
                        🌱 Carbon Impact Calculator
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Calculator */}
                        <div className="bg-white rounded-lg p-6 border border-border-subtle">
                            <label className="block text-sm font-semibold text-ink-default mb-3">
                                Energy Savings (kWh)
                            </label>
                            <input
                                type="number"
                                placeholder="Enter energy saved in kWh"
                                onChange={(e) => e.target.value && calculateCarbonSavings(parseFloat(e.target.value))}
                                className="w-full px-4 py-2 border border-border-subtle rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 mb-4"
                            />
                            <button
                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 rounded-lg transition-colors"
                                onClick={() => {
                                    const input = document.querySelector('input[type="number"]')
                                    if (input?.value) calculateCarbonSavings(parseFloat(input.value))
                                }}
                            >
                                Calculate Impact
                            </button>
                        </div>

                        {/* Impact Results */}
                        {carbonImpact && (
                            <div className="bg-white rounded-lg p-6 border border-border-subtle">
                                <h3 className="font-semibold text-ink-default mb-4">Impact Metrics</h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-ink-faint">🌳 Trees Planted</span>
                                        <span className="font-bold text-emerald-600">{carbonImpact.trees_equivalent}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-ink-faint">🚗 Car Km Avoided</span>
                                        <span className="font-bold text-emerald-600">{carbonImpact.car_km_avoided?.toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-ink-faint">📱 Smartphones Charged</span>
                                        <span className="font-bold text-emerald-600">{carbonImpact.smartphone_charges}</span>
                                    </div>
                                    <div className="flex justify-between items-center pt-3 border-t">
                                        <span className="text-ink-default font-semibold">💨 CO₂ Avoided (kg)</span>
                                        <span className="font-bold text-lg text-emerald-600">{carbonImpact.co2_saved_kg?.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
