import { useState } from 'react'
import { generateWeeklyDigest, downloadDigestPDF } from '../services/api'

const WeeklyDigest = () => {
    const [isGenerating, setIsGenerating] = useState(false)
    const [digest, setDigest] = useState(null)
    const [showModal, setShowModal] = useState(false)

    const handleGenerate = async () => {
        setIsGenerating(true)
        try {
            const data = await generateWeeklyDigest()
            setDigest(data)
            setShowModal(true)
        } catch (error) {
            console.error('Failed to generate digest:', error)
        } finally {
            setIsGenerating(false)
        }
    }

    const handleDownloadPDF = () => {
        downloadDigestPDF()
    }

    return (
        <>
            {/* Generate Button - Place this in your dashboard or header */}
            <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="group flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-xl font-medium shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-all disabled:opacity-60"
            >
                {isGenerating ? (
                    <>
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Generating...
                    </>
                ) : (
                    <>
                        <svg className="w-5 h-5 group-hover:rotate-12 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Generate Weekly Digest
                    </>
                )}
            </button>

            {/* Digest Modal */}
            {showModal && digest && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-3xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden animate-slideUp">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-violet-500 to-purple-600 p-6">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                                        <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-white">{digest.title}</h2>
                                        <p className="text-violet-100 text-sm">AI-Generated Sustainability Report</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleDownloadPDF}
                                        className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-xl text-sm font-medium transition-colors flex items-center gap-2 backdrop-blur-sm"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        Download PDF
                                    </button>
                                    <button
                                        onClick={() => setShowModal(false)}
                                        className="p-2 hover:bg-white/20 rounded-xl transition-colors"
                                    >
                                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
                            {/* Narrative Summary */}
                            <div className="mb-8">
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="text-2xl">✨</span>
                                    <h3 className="text-lg font-bold text-slate-800">Executive Summary</h3>
                                </div>
                                <div className="bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-100 rounded-2xl p-5">
                                    <p className="text-slate-700 leading-relaxed text-lg">
                                        {digest.narrative}
                                    </p>
                                </div>
                            </div>

                            {/* Key Stats */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                                <div className="bg-emerald-50 rounded-2xl p-4 border border-emerald-100">
                                    <p className="text-xs font-semibold text-emerald-600 mb-1">ENERGY SAVED</p>
                                    <p className="text-2xl font-bold text-emerald-700">{digest.stats.total_savings_kwh} <span className="text-sm font-normal">kWh</span></p>
                                </div>
                                <div className="bg-emerald-50 rounded-2xl p-4 border border-emerald-100">
                                    <p className="text-xs font-semibold text-emerald-600 mb-1">COST SAVED</p>
                                    <p className="text-2xl font-bold text-emerald-700">₹{digest.stats.total_savings_inr.toLocaleString()}</p>
                                </div>
                                <div className="bg-sky-50 rounded-2xl p-4 border border-sky-100">
                                    <p className="text-xs font-semibold text-sky-600 mb-1">CO₂ REDUCED</p>
                                    <p className="text-2xl font-bold text-sky-700">{digest.stats.co2_saved_kg} <span className="text-sm font-normal">kg</span></p>
                                </div>
                                <div className="bg-amber-50 rounded-2xl p-4 border border-amber-100">
                                    <p className="text-xs font-semibold text-amber-600 mb-1">EFFICIENCY</p>
                                    <p className="text-2xl font-bold text-amber-700">+{digest.stats.efficiency_change_pct}%</p>
                                </div>
                            </div>

                            {/* Highlights */}
                            <div className="mb-8">
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="text-2xl">🎯</span>
                                    <h3 className="text-lg font-bold text-slate-800">Key Highlights</h3>
                                </div>
                                <div className="space-y-3">
                                    {digest.highlights.map((highlight, idx) => (
                                        <div
                                            key={idx}
                                            className={`flex items-start gap-4 p-4 rounded-xl border ${
                                                highlight.type === 'win'
                                                    ? 'bg-emerald-50 border-emerald-100'
                                                    : highlight.type === 'alert'
                                                        ? 'bg-red-50 border-red-100'
                                                        : 'bg-sky-50 border-sky-100'
                                            }`}
                                        >
                                            <span className="text-2xl">
                                                {highlight.type === 'win' ? '🏆' : highlight.type === 'alert' ? '⚠️' : '💡'}
                                            </span>
                                            <div>
                                                <p className={`font-semibold ${
                                                    highlight.type === 'win'
                                                        ? 'text-emerald-800'
                                                        : highlight.type === 'alert'
                                                            ? 'text-red-800'
                                                            : 'text-sky-800'
                                                }`}>
                                                    {highlight.type === 'win' ? 'Win' : highlight.type === 'alert' ? 'Alert' : 'Insight'}
                                                </p>
                                                <p className="text-slate-600">{highlight.text}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Deep Insights */}
                            <div>
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="text-2xl">🔍</span>
                                    <h3 className="text-lg font-bold text-slate-800">AI Deep Insights</h3>
                                </div>
                                <div className="space-y-3">
                                    {digest.insights.map((insight, idx) => (
                                        <div key={idx} className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
                                            <svg className="w-5 h-5 text-violet-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                            </svg>
                                            <p className="text-slate-700">{insight}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                            <p className="text-xs text-slate-400">
                                Generated by Urja AI • {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                            </p>
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                                AI-Verified Data
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

export default WeeklyDigest
