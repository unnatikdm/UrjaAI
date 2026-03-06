import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import ChatModal from '../components/ChatModal'
import { getDeepRecommendations } from '../services/api'

export default function DeepRecommendations() {
    const { buildingId } = useParams()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [recommendations, setRecommendations] = useState([])
    const [error, setError] = useState(null)
    const [selectedRec, setSelectedRec] = useState(null)
    const [isChatOpen, setIsChatOpen] = useState(false)

    useEffect(() => {
        async function fetchDeepRecs() {
            setLoading(true)
            setError(null)
            try {
                const data = await getDeepRecommendations(buildingId)
                setRecommendations(data)
            } catch (err) {
                console.error('Deep Analysis Error:', err)
                const msg = err.response?.data?.detail || err.message || 'Failed to fetch deep analysis'
                setError(msg)
            } finally {
                setLoading(false)
            }
        }

        fetchDeepRecs()
    }, [buildingId])

    return (
        <div className="min-h-screen bg-beige-light flex flex-col">
            <header className="bg-white border-b border-border px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => navigate(-1)}
                        className="p-2 hover:bg-beige rounded-lg transition-colors"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                        </svg>
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-ink">Deep AI Analysis</h1>
                        <p className="text-xs text-ink-muted">Building: {buildingId?.replace('_', ' ').toUpperCase()}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary-dark rounded-full text-xs font-bold uppercase tracking-wider">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                    </span>
                    RAG-Enriched Intelligence
                </div>
            </header>

            <main className="flex-1 max-w-4xl mx-auto w-full p-6 space-y-8">
                {loading ? (
                    <div className="space-y-6">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-48 bg-white border border-border rounded-2xl animate-pulse" />
                        ))}
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 text-red-600 rounded-2xl p-8 text-center">
                        <p className="font-bold text-lg mb-2">Analysis Failed</p>
                        <p className="text-sm">{error}</p>
                        <button 
                            onClick={() => window.location.reload()}
                            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium"
                        >
                            Retry
                        </button>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <div className="bg-white border border-border rounded-2xl p-6 shadow-sm">
                            <h2 className="text-lg font-bold text-ink mb-1">RAG Pipeline Insights</h2>
                            <p className="text-sm text-ink-muted mb-6">
                                Our Retrieval-Augmented Generation system combines real-time sensor data with historical energy patterns and weather archives to provide deeper context for each optimization action.
                            </p>

                            <div className="space-y-6">
                                {recommendations.map((rec, idx) => (
                                    <div key={idx} className="bg-beige/30 border border-border-subtle rounded-xl p-6 relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 p-4">
                                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-tighter ${
                                                rec.priority === 'high' ? 'bg-red-100 text-red-600' : 
                                                rec.priority === 'medium' ? 'bg-orange-100 text-orange-600' : 
                                                'bg-blue-100 text-blue-600'
                                            }`}>
                                                {rec.priority} PRIORITY
                                            </span>
                                        </div>

                                        <h3 className="text-md font-bold text-ink mb-3 pr-20">{rec.action}</h3>
                                        
                                        <div className="grid grid-cols-2 gap-4 mb-4">
                                            <div className="bg-white p-3 rounded-lg border border-border-subtle">
                                                <p className="text-[10px] text-ink-faint uppercase font-bold">Estimated Savings</p>
                                                <p className="text-lg font-bold text-primary-dark">↓ {rec.savings_kwh} kWh</p>
                                            </div>
                                            <div className="bg-white p-3 rounded-lg border border-border-subtle">
                                                <p className="text-[10px] text-ink-faint uppercase font-bold">Cost Recovery</p>
                                                <p className="text-lg font-bold text-ink">≈ ₹{rec.savings_cost_inr.toFixed(0)}</p>
                                            </div>
                                        </div>

                                        <div className="bg-white/80 rounded-xl p-4 border border-primary-light/30">
                                            <p className="text-xs font-bold text-primary mb-2 flex items-center gap-1.5">
                                                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                                </svg>
                                                Deep AI Justification
                                            </p>
                                            <div className="text-sm text-ink-soft whitespace-pre-wrap leading-relaxed">
                                                {rec.reason}
                                            </div>
                                        </div>
                                        
                                        {rec.sources && rec.sources.length > 0 && (
                                            <div className="mt-4 flex items-center gap-2">
                                                <p className="text-[10px] text-ink-faint font-bold uppercase">Sources:</p>
                                                {rec.sources.map(s => (
                                                    <span key={s} className="px-2 py-0.5 bg-ink/5 text-ink-muted rounded text-[10px] lowercase italic">
                                                        #{s}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                        
                                        {/* Talk to AI Button */}
                                        <button
                                            onClick={() => {
                                                setSelectedRec(rec)
                                                setIsChatOpen(true)
                                            }}
                                            className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors font-medium text-sm"
                                        >
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                            </svg>
                                            Talk to AI about this recommendation
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </main>
            
            {/* Chat Modal */}
            <ChatModal
                isOpen={isChatOpen}
                onClose={() => setIsChatOpen(false)}
                recommendation={selectedRec}
            />
        </div>
    )
}
