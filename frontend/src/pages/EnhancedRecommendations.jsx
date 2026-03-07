import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
    getEnhancedRecommendations, 
    getPricingContext, 
    getWeatherAlerts,
    getOccupancy,
    submitFeedback
} from '../services/api'

// Feedback Modal Component
function FeedbackModal({ isOpen, onClose, recommendation, buildingId, onSubmit }) {
    const [wasHelpful, setWasHelpful] = useState(null)
    const [rating, setRating] = useState(0)
    const [feedbackText, setFeedbackText] = useState('')
    const [actualSavings, setActualSavings] = useState('')
    const [submitting, setSubmitting] = useState(false)

    if (!isOpen || !recommendation) return null

    const handleSubmit = async () => {
        setSubmitting(true)
        try {
            await submitFeedback(
                recommendation.id,
                buildingId,
                wasHelpful,
                feedbackText,
                actualSavings ? parseFloat(actualSavings) : null,
                rating > 0 ? rating : null
            )
            onSubmit()
            onClose()
        } catch (e) {
            console.error('Feedback error:', e)
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full m-4">
                <h3 className="text-lg font-semibold mb-4">Was this recommendation helpful?</h3>
                
                <div className="flex gap-2 mb-4">
                    <button
                        onClick={() => setWasHelpful(true)}
                        className={`flex-1 py-2 rounded-lg border ${wasHelpful === true ? 'bg-green-500 text-white border-green-500' : 'border-gray-300'}`}
                    >
                        👍 Yes
                    </button>
                    <button
                        onClick={() => setWasHelpful(false)}
                        className={`flex-1 py-2 rounded-lg border ${wasHelpful === false ? 'bg-red-500 text-white border-red-500' : 'border-gray-300'}`}
                    >
                        👎 No
                    </button>
                </div>

                {wasHelpful !== null && (
                    <>
                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Rating (1-5)</label>
                            <div className="flex gap-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                    <button
                                        key={star}
                                        onClick={() => setRating(star)}
                                        className={`text-2xl ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
                                    >
                                        ★
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Actual savings (kWh) - optional</label>
                            <input
                                type="number"
                                value={actualSavings}
                                onChange={(e) => setActualSavings(e.target.value)}
                                className="w-full border rounded-lg px-3 py-2"
                                placeholder="e.g., 0.8"
                            />
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Comments (optional)</label>
                            <textarea
                                value={feedbackText}
                                onChange={(e) => setFeedbackText(e.target.value)}
                                className="w-full border rounded-lg px-3 py-2"
                                rows={3}
                                placeholder="Tell us more about your experience..."
                            />
                        </div>

                        <button
                            onClick={handleSubmit}
                            disabled={submitting}
                            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                        >
                            {submitting ? 'Submitting...' : 'Submit Feedback'}
                        </button>
                    </>
                )}

                <button
                    onClick={onClose}
                    className="w-full mt-2 text-gray-500 hover:text-gray-700"
                >
                    Cancel
                </button>
            </div>
        </div>
    )
}

export default function EnhancedRecommendations() {
    const { buildingId } = useParams()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [recommendations, setRecommendations] = useState([])
    const [pricingContext, setPricingContext] = useState(null)
    const [weatherAlerts, setWeatherAlerts] = useState([])
    const [occupancy, setOccupancy] = useState(null)
    const [error, setError] = useState(null)
    const [selectedRec, setSelectedRec] = useState(null)
    const [feedbackRec, setFeedbackRec] = useState(null)
    const [feedbackSubmitted, setFeedbackSubmitted] = useState({})

    useEffect(() => {
        async function fetchData() {
            setLoading(true)
            setError(null)
            try {
                // Fetch all data in parallel
                const [recsData, pricingData, weatherData, occupancyData] = await Promise.all([
                    getEnhancedRecommendations(buildingId),
                    getPricingContext(),
                    getWeatherAlerts(),
                    getOccupancy(buildingId)
                ])

                setRecommendations(recsData.recommendations || [])
                setPricingContext(pricingData)
                setWeatherAlerts(weatherData.alerts || [])
                setOccupancy(occupancyData)
            } catch (err) {
                console.error('Enhanced Recommendations Error:', err)
                setError(err.response?.data?.detail || err.message || 'Failed to fetch enhanced recommendations')
            } finally {
                setLoading(false)
            }
        }

        if (buildingId) {
            fetchData()
        }
    }, [buildingId])

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'bg-red-100 text-red-800 border-red-200'
            case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
            case 'low': return 'bg-green-100 text-green-800 border-green-200'
            default: return 'bg-gray-100 text-gray-800 border-gray-200'
        }
    }

    const getPriorityScoreColor = (score) => {
        if (score >= 80) return 'text-red-600'
        if (score >= 60) return 'text-yellow-600'
        return 'text-green-600'
    }

    if (loading) {
        return (
            <div className="p-6 max-w-7xl mx-auto">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-6 max-w-7xl mx-auto">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h2 className="text-red-800 font-semibold mb-2">Error Loading Recommendations</h2>
                    <p className="text-red-600">{error}</p>
                    <button 
                        onClick={() => navigate('/buildings')}
                        className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                        Back to Buildings
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Enhanced Recommendations
                        </h1>
                        <p className="text-gray-600 mt-1">
                            Building {buildingId} • Real-time context enriched
                        </p>
                    </div>
                    <button
                        onClick={() => navigate(`/buildings/${buildingId}`)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                        ← Back to Building
                    </button>
                </div>
            </div>

            {/* Context Bar */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {/* Pricing Context */}
                {pricingContext && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h3 className="text-sm font-semibold text-blue-800 mb-2">⚡ Current Energy Pricing</h3>
                        <div className="space-y-1 text-sm">
                            <p className="flex justify-between">
                                <span>Current Rate:</span>
                                <span className="font-semibold">₹{pricingContext.current_rate_inr_per_kwh}/kWh</span>
                            </p>
                            <p className="flex justify-between">
                                <span>Period:</span>
                                <span className="capitalize">{pricingContext.current_period}</span>
                            </p>
                            <div className="mt-2 pt-2 border-t border-blue-200 text-xs text-blue-600">
                                Peak: ₹{pricingContext.peak_rate} • Off-peak: ₹{pricingContext.off_peak_rate}
                            </div>
                        </div>
                    </div>
                )}

                {/* Occupancy */}
                {occupancy && (
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <h3 className="text-sm font-semibold text-purple-800 mb-2">👥 Occupancy Status</h3>
                        <div className="space-y-1 text-sm">
                            <div className="flex items-center justify-between">
                                <span>Current:</span>
                                <span className={`font-semibold ${
                                    occupancy.occupancy_percentage > 70 ? 'text-red-600' : 
                                    occupancy.occupancy_percentage > 40 ? 'text-yellow-600' : 'text-green-600'
                                }`}>
                                    {occupancy.occupancy_percentage}%
                                </span>
                            </div>
                            <p className="flex justify-between">
                                <span>Level:</span>
                                <span className="capitalize">{occupancy.occupancy_level}</span>
                            </p>
                            <p className="text-xs text-purple-600 mt-2">
                                Based on: {occupancy.data_sources?.join(', ')}
                            </p>
                        </div>
                    </div>
                )}

                {/* Weather Alerts */}
                <div className={`border rounded-lg p-4 ${weatherAlerts.length > 0 ? 'bg-orange-50 border-orange-200' : 'bg-green-50 border-green-200'}`}>
                    <h3 className={`text-sm font-semibold mb-2 ${weatherAlerts.length > 0 ? 'text-orange-800' : 'text-green-800'}`}>
                        🌤️ Weather Status
                    </h3>
                    {weatherAlerts.length > 0 ? (
                        <div className="space-y-2">
                            {weatherAlerts.slice(0, 2).map((alert, idx) => (
                                <div key={idx} className="text-sm text-orange-700">
                                    <span className="font-semibold capitalize">{alert.type}:</span> {alert.message}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-green-700">No weather alerts. Normal conditions expected.</p>
                    )}
                </div>
            </div>

            {/* Recommendations */}
            <div className="space-y-4">
                <h2 className="text-lg font-semibold text-gray-900">
                    Smart Recommendations ({recommendations.length})
                </h2>

                {recommendations.map((rec) => (
                    <div 
                        key={rec.id}
                        className={`bg-white rounded-lg shadow-md border-2 transition-all cursor-pointer ${
                            selectedRec?.id === rec.id ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedRec(selectedRec?.id === rec.id ? null : rec)}
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-gray-100">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${getPriorityColor(rec.priority)}`}>
                                            {rec.priority.toUpperCase()}
                                        </span>
                                        <span className={`text-sm font-semibold ${getPriorityScoreColor(rec.priority_score)}`}>
                                            Score: {rec.priority_score}/100
                                        </span>
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-900">{rec.action}</h3>
                                </div>
                                <div className="text-right">
                                    <div className="text-2xl font-bold text-green-600">
                                        ₹{rec.savings?.total_monthly_savings?.toFixed(0)}
                                    </div>
                                    <div className="text-sm text-gray-500">monthly savings</div>
                                </div>
                            </div>
                        </div>

                        {/* Quick Stats */}
                        <div className="px-4 py-3 bg-gray-50 grid grid-cols-3 gap-4 text-center">
                            <div>
                                <div className="text-lg font-semibold text-blue-600">
                                    {rec.savings?.energy_kwh} kWh
                                </div>
                                <div className="text-xs text-gray-500">Energy Saved</div>
                            </div>
                            <div>
                                <div className="text-lg font-semibold text-green-600">
                                    ₹{rec.savings?.cost_inr}
                                </div>
                                <div className="text-xs text-gray-500">Cost Savings</div>
                            </div>
                            <div>
                                <div className="text-lg font-semibold text-purple-600">
                                    {rec.savings?.demand_charge_savings ? 
                                        `₹${rec.savings.demand_charge_savings.monthly_demand_savings}` : 
                                        'N/A'
                                    }
                                </div>
                                <div className="text-xs text-gray-500">Demand Savings</div>
                            </div>
                        </div>

                        {/* Expanded Details */}
                        {selectedRec?.id === rec.id && (
                            <div className="p-4 border-t border-gray-200 space-y-4">
                                {/* Enhanced Text */}
                                <div className="prose prose-sm max-w-none">
                                    <div 
                                        className="text-gray-700 whitespace-pre-line"
                                        dangerouslySetInnerHTML={{ 
                                            __html: rec.enhanced_text?.replace(/\*\*/g, '').replace(/•/g, '&bull;') 
                                        }}
                                    />
                                </div>

                                {/* Benchmarks */}
                                {rec.benchmarks && (
                                    <div className="bg-green-50 rounded-lg p-4">
                                        <h4 className="font-semibold text-green-800 mb-2">🌍 Environmental Impact</h4>
                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <span className="text-green-700">CO₂ Saved:</span>
                                                <span className="ml-2 font-semibold">{rec.benchmarks.environmental.co2_saved_grams}g</span>
                                            </div>
                                            <div>
                                                <span className="text-green-700">Trees:</span>
                                                <span className="ml-2 font-semibold">{rec.benchmarks.environmental.trees_equivalent}</span>
                                            </div>
                                            <div>
                                                <span className="text-green-700">Car KM Avoided:</span>
                                                <span className="ml-2 font-semibold">{rec.benchmarks.environmental.car_km_avoided}</span>
                                            </div>
                                            <div>
                                                <span className="text-green-700">Smartphone Charges:</span>
                                                <span className="ml-2 font-semibold">{rec.benchmarks.household_equivalents?.smartphone_charges}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Action Levels */}
                                {rec.action_levels && (
                                    <div className="bg-blue-50 rounded-lg p-4">
                                        <h4 className="font-semibold text-blue-800 mb-2">📊 Action Levels</h4>
                                        <div className="space-y-2">
                                            {rec.action_levels.map((level, idx) => (
                                                <div 
                                                    key={idx}
                                                    className={`flex items-center justify-between p-2 rounded ${
                                                        level.recommendation === 'recommended' ? 
                                                            'bg-blue-100 border border-blue-300' : 'bg-white'
                                                    }`}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-semibold text-blue-900">{level.level}</span>
                                                        <span className="text-blue-700">{level.setpoint_change}</span>
                                                        {level.recommendation === 'recommended' && (
                                                            <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded">⭐ Recommended</span>
                                                        )}
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="font-semibold text-green-600">₹{level.cost_saved_inr}</span>
                                                        <span className="text-xs text-gray-500 ml-1">({level.comfort_impact})</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Historical Validation */}
                                {rec.historical_validation && (
                                    <div className="bg-purple-50 rounded-lg p-4">
                                        <h4 className="font-semibold text-purple-800 mb-2">📈 Historical Validation</h4>
                                        <div className="text-sm text-purple-700 space-y-1">
                                            <p>Based on {rec.historical_validation.similar_cases} similar cases</p>
                                            <p>Success rate: {(rec.historical_validation.success_rate * 100).toFixed(0)}%</p>
                                            <p>Average actual savings: {rec.historical_validation.avg_actual_savings.toFixed(2)} kWh</p>
                                        </div>
                                    </div>
                                )}

                                {/* Implementation Guide */}
                                {rec.implementation && (
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-semibold text-gray-800 mb-2">🔧 Implementation Guide</h4>
                                        {rec.implementation.automation && (
                                            <div className="mb-3">
                                                <h5 className="font-medium text-gray-700 text-sm mb-1">
                                                    {rec.implementation.automation.title}
                                                </h5>
                                                <ol className="list-decimal list-inside text-sm text-gray-600 space-y-1">
                                                    {rec.implementation.automation.steps.map((step, idx) => (
                                                        <li key={idx}>{step}</li>
                                                    ))}
                                                </ol>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Expand/Collapse Hint */}
                        <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 text-center">
                            <span className="text-xs text-gray-500">
                                {selectedRec?.id === rec.id ? 'Click to collapse ↑' : 'Click for details ↓'}
                            </span>
                        </div>

                        {/* Feedback Section */}
                        <div className="px-4 py-3 bg-blue-50 border-t border-blue-100 flex items-center justify-between">
                            <span className="text-sm text-blue-700">Was this helpful?</span>
                            {feedbackSubmitted[rec.id] ? (
                                <span className="text-sm text-green-600 font-medium">✓ Feedback received!</span>
                            ) : (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        setFeedbackRec(rec)
                                    }}
                                    className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
                                >
                                    Give Feedback
                                </button>
                            )}
                        </div>
                    </div>
                ))}

                {recommendations.length === 0 && (
                    <div className="text-center py-12 bg-gray-50 rounded-lg">
                        <p className="text-gray-500">No recommendations available at this time.</p>
                    </div>
                )}
            </div>

            {/* Feedback Modal */}
            <FeedbackModal
                isOpen={!!feedbackRec}
                onClose={() => setFeedbackRec(null)}
                recommendation={feedbackRec}
                buildingId={buildingId}
                onSubmit={() => {
                    if (feedbackRec) {
                        setFeedbackSubmitted({ ...feedbackSubmitted, [feedbackRec.id]: true })
                    }
                }}
            />
        </div>
    )
}
