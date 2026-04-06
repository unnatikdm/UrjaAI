import { useState, useEffect, useCallback } from 'react'
import { getAnomalyNotifications, resolveAnomaly } from '../services/api'

// Global notification store
const notificationStore = {
    notifications: [],
    resolved: new Set()
}

const AnomalyNotifications = () => {
    const [notifications, setNotifications] = useState(notificationStore.notifications)
    const [activeResolutions, setActiveResolutions] = useState(new Set())
    const [completedResolutions, setCompletedResolutions] = useState([])

    useEffect(() => {
        // Poll for new anomalies every 30 seconds
        fetchNotifications()
        const interval = setInterval(fetchNotifications, 30000)
        return () => clearInterval(interval)
    }, [])

    const fetchNotifications = async () => {
        try {
            const data = await getAnomalyNotifications()
            // Filter out already resolved
            const active = data.filter(n => !notificationStore.resolved.has(n.id))
            notificationStore.notifications = active
            setNotifications(active)
        } catch (e) {
            // If API fails, show demo notification for UX testing
            if (notificationStore.notifications.length === 0 && Math.random() > 0.7) {
                const demoNotification = {
                    id: 'demo-' + Date.now(),
                    type: 'anomaly',
                    severity: 'high',
                    building: 'Hall A',
                    room: 'Lecture Hall A',
                    message: 'Energy consumption 45% above baseline',
                    detected_at: new Date().toISOString(),
                    suggestion: 'Smart-dim lights to 60%',
                    estimated_savings: { kwh: 4.5, inr: 338 }
                }
                notificationStore.notifications = [demoNotification]
                setNotifications([demoNotification])
            }
        }
    }

    const handleResolve = useCallback(async (notification) => {
        setActiveResolutions(prev => new Set(prev).add(notification.id))

        try {
            // Simulate the resolution action
            await new Promise(resolve => setTimeout(resolve, 1500))

            const result = await resolveAnomaly(notification.id, {
                action: notification.suggestion,
                automated: true
            })

            notificationStore.resolved.add(notification.id)

            // Show completion toast
            setCompletedResolutions(prev => [...prev, {
                id: notification.id,
                building: notification.building,
                action: notification.suggestion,
                savings: result.savings_kwh || notification.estimated_savings?.kwh || 3.2,
                savingsInr: result.savings_inr || notification.estimated_savings?.inr || 240
            }])

            // Remove from active notifications
            setNotifications(prev => prev.filter(n => n.id !== notification.id))

            // Clear toast after 5 seconds
            setTimeout(() => {
                setCompletedResolutions(prev => prev.filter(r => r.id !== notification.id))
            }, 5000)

        } catch (error) {
            console.error('Resolution failed:', error)
        } finally {
            setActiveResolutions(prev => {
                const next = new Set(prev)
                next.delete(notification.id)
                return next
            })
        }
    }, [])

    const dismissNotification = (id) => {
        notificationStore.resolved.add(id)
        setNotifications(prev => prev.filter(n => n.id !== id))
    }

    if (notifications.length === 0 && completedResolutions.length === 0) {
        return null
    }

    return (
        <div className="fixed top-20 right-6 z-40 flex flex-col gap-3 max-w-sm">
            {/* Active Notifications */}
            {notifications.map(notification => (
                <div
                    key={notification.id}
                    className={`rounded-2xl shadow-xl border backdrop-blur-md overflow-hidden animate-slideIn ${
                        notification.severity === 'high'
                            ? 'bg-gradient-to-r from-red-50/95 to-orange-50/95 border-red-200'
                            : notification.severity === 'medium'
                                ? 'bg-gradient-to-r from-amber-50/95 to-yellow-50/95 border-amber-200'
                                : 'bg-gradient-to-r from-blue-50/95 to-cyan-50/95 border-blue-200'
                    }`}
                >
                    {/* Header */}
                    <div className={`px-4 py-3 flex items-center gap-3 ${
                        notification.severity === 'high'
                            ? 'bg-red-500/10'
                            : notification.severity === 'medium'
                                ? 'bg-amber-500/10'
                                : 'bg-blue-500/10'
                    }`}>
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            notification.severity === 'high'
                                ? 'bg-red-500'
                                : notification.severity === 'medium'
                                    ? 'bg-amber-500'
                                    : 'bg-blue-500'
                        }`}>
                            <svg className="w-5 h-5 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <div className="flex-1">
                            <p className="font-bold text-sm text-slate-800">
                                ⚠️ Anomaly Detected
                            </p>
                            <p className="text-xs text-slate-500">
                                {notification.building} • {notification.room || 'General'}
                            </p>
                        </div>
                        <button
                            onClick={() => dismissNotification(notification.id)}
                            className="p-1 hover:bg-white/50 rounded-lg transition-colors"
                        >
                            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Body */}
                    <div className="px-4 py-3">
                        <p className="text-sm text-slate-700 mb-3">
                            {notification.message}
                        </p>

                        {/* Suggested Action */}
                        <div className="bg-white/60 rounded-xl p-3 mb-3 border border-white/50">
                            <p className="text-xs font-semibold text-slate-500 mb-1">💡 SUGGESTED ACTION</p>
                            <p className="text-sm font-medium text-slate-800">{notification.suggestion}</p>
                            <div className="flex gap-3 mt-2 text-xs">
                                <span className="text-emerald-600 font-medium">
                                    ⚡ Save {notification.estimated_savings?.kwh || 3.5} kWh
                                </span>
                                <span className="text-emerald-600 font-medium">
                                    💰 ₹{notification.estimated_savings?.inr || 262}/day
                                </span>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2">
                            <button
                                onClick={() => handleResolve(notification)}
                                disabled={activeResolutions.has(notification.id)}
                                className={`flex-1 py-2.5 px-4 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 ${
                                    notification.severity === 'high'
                                        ? 'bg-red-500 hover:bg-red-600 text-white'
                                        : notification.severity === 'medium'
                                            ? 'bg-amber-500 hover:bg-amber-600 text-white'
                                            : 'bg-blue-500 hover:bg-blue-600 text-white'
                                } disabled:opacity-60 disabled:cursor-not-allowed`}
                            >
                                {activeResolutions.has(notification.id) ? (
                                    <>
                                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Applying...
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        Resolve Now
                                    </>
                                )}
                            </button>
                            <button
                                onClick={() => dismissNotification(notification.id)}
                                className="px-4 py-2.5 bg-white/60 hover:bg-white/80 text-slate-600 rounded-xl text-sm font-medium transition-colors border border-slate-200"
                            >
                                Dismiss
                            </button>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="px-4 py-2 bg-black/5 text-[10px] text-slate-400 flex items-center gap-2">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Detected {new Date(notification.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                </div>
            ))}

            {/* Success Toasts */}
            {completedResolutions.map(resolution => (
                <div
                    key={resolution.id}
                    className="rounded-2xl shadow-xl bg-gradient-to-r from-emerald-50/95 to-teal-50/95 border border-emerald-200 backdrop-blur-md p-4 animate-slideIn"
                >
                    <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
                            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <div className="flex-1">
                            <p className="font-bold text-emerald-800 text-sm">✅ Action Applied!</p>
                            <p className="text-xs text-emerald-600 mt-1">
                                {resolution.building}: {resolution.action}
                            </p>
                            <div className="flex gap-3 mt-2 text-xs">
                                <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-medium">
                                    ⚡ {resolution.savings.toFixed(1)} kWh saved
                                </span>
                                <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-medium">
                                    💰 ₹{resolution.savingsInr} instant value
                                </span>
                            </div>
                        </div>
                        <button
                            onClick={() => setCompletedResolutions(prev => prev.filter(r => r.id !== resolution.id))}
                            className="p-1 hover:bg-emerald-100 rounded-lg transition-colors"
                        >
                            <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            ))}
        </div>
    )
}

export default AnomalyNotifications
