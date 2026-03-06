import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

export default function Browniepoint2({ selectedBuilding }) {
    const [systemInfo, setSystemInfo] = useState(null)
    const [prediction, setPrediction] = useState(null)
    const [explanation, setExplanation] = useState(null)
    const [leaderboard, setLeaderboard] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [activeSection, setActiveSection] = useState('overview')
    const [features, setFeatures] = useState({})

    useEffect(() => {
        fetchBrowniepoint2Data()
    }, [selectedBuilding])

    const fetchBrowniepoint2Data = async () => {
        setLoading(true)
        try {
            const [infoRes, leaderboardRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/browniepoint2/system-info`),
                axios.get(`${API_BASE_URL}/browniepoint2/leaderboard`)
            ])

            setSystemInfo(infoRes.data)
            setLeaderboard(leaderboardRes.data?.leaderboard || [])
            setError(null)
        } catch (err) {
            console.error('Error fetching browniepoint2 data:', err)
            setError('Failed to load TabTransformer ML platform')
        } finally {
            setLoading(false)
        }
    }

    const makePrediction = async () => {
        try {
            setLoading(true)
            const res = await axios.post(`${API_BASE_URL}/browniepoint2/predict`, {
                features: features,
                explain: true,
                user_id: 'demo-user',
                top_k_features: 10
            })
            setPrediction(res.data)
            setExplanation(res.data.explanation)
            setError(null)
        } catch (err) {
            console.error('Error making prediction:', err)
            setError('Failed to make prediction')
        } finally {
            setLoading(false)
        }
    }

    if (loading && !systemInfo) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-ink-default">Loading TabTransformer ML Platform...</p>
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
            <div className="flex gap-2 border-b border-border-subtle overflow-x-auto">
                {['overview', 'predict', 'leaderboard', 'explainability'].map(section => (
                    <button
                        key={section}
                        onClick={() => setActiveSection(section)}
                        className={`pb-3 px-4 font-medium transition-colors capitalize whitespace-nowrap ${
                            activeSection === section
                                ? 'text-blue-600 border-b-2 border-blue-600'
                                : 'text-ink-faint hover:text-ink-default'
                        }`}
                    >
                        {section === 'overview' && '📊 Overview'}
                        {section === 'predict' && '🔮 Make Prediction'}
                        {section === 'leaderboard' && '🏆 Leaderboard'}
                        {section === 'explainability' && '🔍 Explainability'}
                    </button>
                ))}
            </div>

            {/* Overview Section */}
            {activeSection === 'overview' && systemInfo && (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {/* Model Info Card */}
                        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-border-subtle">
                            <h3 className="text-lg font-bold text-ink-default mb-4">🤖 Model Architecture</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Type</span>
                                    <span className="font-medium text-ink-default">{systemInfo.model_info?.model_type || 'TabTransformer'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Embeddings</span>
                                    <span className="font-medium text-ink-default">{systemInfo.model_info?.embedding_dim || '16'}-dim</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Depth</span>
                                    <span className="font-medium text-ink-default">{systemInfo.model_info?.depth || '6'} layers</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Attention Heads</span>
                                    <span className="font-medium text-ink-default">{systemInfo.model_info?.num_heads || '8'}</span>
                                </div>
                            </div>
                        </div>

                        {/* Features Card */}
                        <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-6 border border-border-subtle">
                            <h3 className="text-lg font-bold text-ink-default mb-4">📈 Features</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Categorical</span>
                                    <span className="font-medium text-ink-default">{systemInfo.features?.categorical_features || '69'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Total Features</span>
                                    <span className="font-medium text-ink-default">{systemInfo.features?.total_features || '69'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Training Samples</span>
                                    <span className="font-medium text-ink-default">{systemInfo.features?.training_samples || '5000'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Target Task</span>
                                    <span className="font-medium text-ink-default">CARAVAN</span>
                                </div>
                            </div>
                        </div>

                        {/* System Stats Card */}
                        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-border-subtle">
                            <h3 className="text-lg font-bold text-ink-default mb-4">⚙️ System Stats</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Status</span>
                                    <span className="font-medium text-emerald-600">🟢 Ready</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Model Status</span>
                                    <span className="font-medium text-emerald-600">✓ Loaded</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Explanations</span>
                                    <span className="font-medium text-emerald-600">✓ Enabled</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-ink-faint">Badges Available</span>
                                    <span className="font-medium text-ink-default">{systemInfo.badges_count || '0'}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Business Context */}
                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-border-subtle">
                        <h3 className="text-lg font-bold text-ink-default mb-4">🎯 Business Context</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h4 className="font-semibold text-ink-default mb-2">Dataset: COIL 2000</h4>
                                <p className="text-sm text-ink-faint mb-3">
                                    Real-world insurance customer dataset with 69 demographic and product features.
                                </p>
                                <ul className="text-sm space-y-1 text-ink-default">
                                    <li>✓ 5,000 customer records</li>
                                    <li>✓ 69 categorical features</li>
                                    <li>✓ Insurance prediction target (CARAVAN)</li>
                                    <li>✓ Realistic data distribution</li>
                                </ul>
                            </div>
                            <div>
                                <h4 className="font-semibold text-ink-default mb-2">Use Case: Customer Targeting</h4>
                                <p className="text-sm text-ink-faint mb-3">
                                    Identify high-propensity customers for insurance product targeting.
                                </p>
                                <ul className="text-sm space-y-1 text-ink-default">
                                    <li>✓ Actionable predictions</li>
                                    <li>✓ Explainable recommendations</li>
                                    <li>✓ Compliance-ready (SHAP)</li>
                                    <li>✓ Gamification framework</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Prediction Section */}
            {activeSection === 'predict' && (
                <div className="space-y-6">
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                        <h3 className="text-xl font-bold text-ink-default mb-4">🔮 Make a Prediction</h3>
                        <p className="text-ink-faint mb-6">
                            The model will predict insurance customer propensity based on demographic features.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            {/* Sample Feature Inputs */}
                            <div>
                                <label className="block text-sm font-semibold text-ink-default mb-2">Customer Age Group</label>
                                <select
                                    onChange={(e) => setFeatures({ ...features, age_group: e.target.value })}
                                    className="w-full px-4 py-2 border border-border-subtle rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Select age group</option>
                                    <option value="young">18-30 (Young)</option>
                                    <option value="middle">31-50 (Middle)</option>
                                    <option value="senior">50+ (Senior)</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-ink-default mb-2">Customer Segment</label>
                                <select
                                    onChange={(e) => setFeatures({ ...features, segment: e.target.value })}
                                    className="w-full px-4 py-2 border border-border-subtle rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Select segment</option>
                                    <option value="premium">Premium</option>
                                    <option value="standard">Standard</option>
                                    <option value="budget">Budget</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-ink-default mb-2">Product Ownership</label>
                                <select
                                    onChange={(e) => setFeatures({ ...features, products: e.target.value })}
                                    className="w-full px-4 py-2 border border-border-subtle rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Number of products</option>
                                    <option value="0">None</option>
                                    <option value="1">1-2 Products</option>
                                    <option value="2">3-5 Products</option>
                                    <option value="3">5+ Products</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-ink-default mb-2">Customer Tenure</label>
                                <select
                                    onChange={(e) => setFeatures({ ...features, tenure: e.target.value })}
                                    className="w-full px-4 py-2 border border-border-subtle rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Select tenure</option>
                                    <option value="new">New (0-1 year)</option>
                                    <option value="established">Established (1-5 years)</option>
                                    <option value="loyal">Loyal (5+ years)</option>
                                </select>
                            </div>
                        </div>

                        <button
                            onClick={makePrediction}
                            disabled={loading}
                            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 rounded-lg transition-colors"
                        >
                            {loading ? 'Making Prediction...' : '🔮 Generate Prediction & Explanation'}
                        </button>
                    </div>

                    {/* Prediction Results */}
                    {prediction && (
                        <div className="bg-white rounded-xl p-6 border-2 border-blue-200">
                            <h4 className="text-xl font-bold text-ink-default mb-4">📊 Prediction Results</h4>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                                <div className="bg-blue-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-ink-faint mb-2">Prediction</p>
                                    <p className="text-3xl font-bold text-blue-600 mb-1">
                                        {prediction.prediction_class === 'insurance' ? '✅ Has Insurance' : '❌ No Insurance'}
                                    </p>
                                    <p className="text-xs text-ink-faint">ID: {prediction.request_id?.substring(0, 8)}</p>
                                </div>

                                <div className="bg-emerald-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-ink-faint mb-2">Probability</p>
                                    <p className="text-3xl font-bold text-emerald-600">
                                        {(prediction.probability * 100).toFixed(1)}%
                                    </p>
                                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                                        <div
                                            className="bg-emerald-600 h-2 rounded-full"
                                            style={{ width: `${prediction.probability * 100}%` }}
                                        ></div>
                                    </div>
                                </div>

                                <div className="bg-purple-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-ink-faint mb-2">Confidence</p>
                                    <p className="text-2xl font-bold text-purple-600 mb-1">{prediction.confidence}</p>
                                    <p className="text-xs text-ink-faint">Processing: {prediction.processing_time_ms?.toFixed(2)}ms</p>
                                </div>
                            </div>

                            {prediction.explanation && (
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <h5 className="font-semibold text-ink-default mb-3">Top Contributing Features</h5>
                                    <div className="space-y-2">
                                        {Object.entries(prediction.explanation)
                                            .slice(0, 5)
                                            .map(([feature, importance], idx) => (
                                                <div key={idx} className="flex items-center justify-between">
                                                    <span className="text-sm text-ink-faint">{feature}</span>
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-40 bg-gray-200 rounded-full h-2">
                                                            <div
                                                                className="bg-blue-600 h-2 rounded-full"
                                                                style={{
                                                                    width: `${Math.min(
                                                                        Math.abs(importance) * 100,
                                                                        100
                                                                    )}%`
                                                                }}
                                                            ></div>
                                                        </div>
                                                        <span className="text-sm font-medium text-ink-default w-12 text-right">
                                                            {importance?.toFixed(2)}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Leaderboard Section */}
            {activeSection === 'leaderboard' && (
                <div className="space-y-4">
                    <h3 className="text-2xl font-bold text-ink-default flex items-center gap-2">🏆 Performance Leaderboard</h3>
                    {leaderboard.length > 0 ? (
                        <div className="bg-white rounded-xl border border-border-subtle overflow-hidden">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-border-subtle">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-ink-default">Rank</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-ink-default">Classification</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-ink-default">User</th>
                                        <th className="px-6 py-3 text-right text-sm font-semibold text-ink-default">Score</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border-subtle">
                                    {leaderboard.slice(0, 10).map((entry, idx) => (
                                        <tr key={idx} className={idx === 0 ? 'bg-amber-50' : idx === 1 ? 'bg-gray-100' : idx === 2 ? 'bg-orange-50' : ''}>
                                            <td className="px-6 py-4 text-sm font-bold text-ink-default">
                                                {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-ink-default">{entry.model_type || 'TabTransformer'}</td>
                                            <td className="px-6 py-4 text-sm text-ink-faint">{entry.user_id || 'System'}</td>
                                            <td className="px-6 py-4 text-sm font-semibold text-ink-default text-right">
                                                {typeof entry.accuracy === 'number' ? (entry.accuracy * 100).toFixed(2) : entry.score}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
                            <p className="text-blue-700 font-semibold">📊 Leaderboard will populate as predictions are made</p>
                        </div>
                    )}
                </div>
            )}

            {/* Explainability Section */}
            {activeSection === 'explainability' && (
                <div className="space-y-6">
                    <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-border-subtle">
                        <h3 className="text-2xl font-bold text-ink-default mb-4 flex items-center gap-2">🔍 Model Explainability</h3>
                        <p className="text-ink-faint mb-6">
                            This platform uses SHAP (SHapley Additive exPlanations) to provide interpretable predictions.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-white rounded-lg p-6 border border-border-subtle">
                                <h4 className="font-semibold text-ink-default mb-3">📈 SHAP Values</h4>
                                <p className="text-sm text-ink-faint mb-4">
                                    SHAP values decompose a prediction into contributions from each feature, enabling:
                                </p>
                                <ul className="text-sm space-y-2 text-ink-default">
                                    <li>✓ Feature importance ranking</li>
                                    <li>✓ Individual prediction explanations</li>
                                    <li>✓ Risk factor identification</li>
                                    <li>✓ Regulatory compliance (interpretability)</li>
                                </ul>
                            </div>

                            <div className="bg-white rounded-lg p-6 border border-border-subtle">
                                <h4 className="font-semibold text-ink-default mb-3">🎯 Use Cases</h4>
                                <p className="text-sm text-ink-faint mb-4">
                                    Explainability enables trustworthy AI applications:
                                </p>
                                <ul className="text-sm space-y-2 text-ink-default">
                                    <li>✓ Business insights discovery</li>
                                    <li>✓ Customer segmentation</li>
                                    <li>✓ Decision justification</li>
                                    <li>✓ Bias detection & mitigation</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    {explanation && (
                        <div className="bg-white rounded-xl p-6 border border-border-subtle">
                            <h4 className="font-semibold text-ink-default mb-4">Feature Contributions</h4>
                            <div className="space-y-3">
                                {Object.entries(explanation)
                                    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                                    .slice(0, 10)
                                    .map(([feature, value], idx) => (
                                        <div key={idx} className="flex items-center gap-4">
                                            <span className="w-32 text-sm font-medium text-ink-default truncate">{feature}</span>
                                            <div className="flex-1">
                                                <div className="flex gap-2">
                                                    <div className="w-32 bg-gray-200 rounded-full h-2">
                                                        <div
                                                            className={`h-2 rounded-full ${value > 0 ? 'bg-emerald-600' : 'bg-red-600'}`}
                                                            style={{
                                                                width: `${Math.min(Math.abs(value) * 100, 100)}%`
                                                            }}
                                                        ></div>
                                                    </div>
                                                    <span className="text-sm font-medium text-ink-default w-16 text-right">
                                                        {value?.toFixed(3)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
