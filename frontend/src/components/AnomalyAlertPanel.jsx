import React, { useState, useEffect } from "react";
import { format } from "date-fns";

/**
 * AnomalyAlertPanel
 * Displays real-time flagged anomalies powered by the Schedule-Aware I-BLEND transfer model.
 */
const AnomalyAlertPanel = () => {
    const [anomalies, setAnomalies] = useState([]);
    const [loading, setLoading] = useState(false);

    // Mock initial fetch simulating real-time websockets or polling to /anomalies/detect
    useEffect(() => {
        const fetchAnomalies = async () => {
            setLoading(true);
            try {
                // In a real flow, this would query a database of recently flagged events.
                // We'll mock a ping to the live detect endpoint to show it works
                const mockPayload = {
                    building_id: "Bosch_A",
                    building_type: "Lecture Hall",
                    timestamp: new Date().toISOString(),
                    actual_consumption: 92.5, // High spike to force a Type A Alert
                };

                const response = await fetch("http://localhost:8000/anomalies/detect", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(mockPayload),
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.is_anomaly) {
                        setAnomalies([
                            {
                                id: Math.random().toString(36).substr(2, 9),
                                timestamp: mockPayload.timestamp,
                                building_id: mockPayload.building_id,
                                ...data,
                            },
                        ]);
                    }
                }
            } catch (err) {
                console.error("Error fetching anomalies:", err);
            }
            setLoading(false);
        };

        fetchAnomalies();

        // Set up polling (e.g. every 30s)
        const interval = setInterval(fetchAnomalies, 30000);
        return () => clearInterval(interval);
    }, []);

    const getSeverityColor = (severity) => {
        switch (severity.toLowerCase()) {
            case "high":
                return "bg-red-900 border-red-500 text-red-100";
            case "medium":
                return "bg-yellow-900 border-yellow-500 text-yellow-100";
            default:
                return "bg-slate-800 border-slate-600 text-slate-300";
        }
    };

    const getAnomalyTypeLabel = (type) => {
        switch (type) {
            case "A": return "Type A: Equipment Fault / Unscheduled High Load";
            case "B": return "Type B: Meter Issue / Data Loss";
            case "C": return "Type C: Schedule Mismatch (Expected high, got low)";
            default: return "Unknown Anomaly";
        }
    };

    return (
        <div className="w-full bg-slate-900 rounded-xl border border-slate-700 p-6 shadow-xl mb-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    <span className="text-red-500">⚠</span> Active Anomalies
                    <span className="text-sm font-normal text-slate-400 bg-slate-800 px-3 py-1 rounded-full">
                        Schedule-Aware Detection
                    </span>
                </h2>
                <div className="text-sm text-slate-400">
                    Last 24h • {anomalies.length} Flags
                </div>
            </div>

            {loading && anomalies.length === 0 ? (
                <div className="text-center py-8 text-slate-500 animate-pulse">
                    Scanning telemetry...
                </div>
            ) : anomalies.length === 0 ? (
                <div className="text-center py-8 text-slate-500 bg-slate-800/50 rounded-lg border border-slate-700/50">
                    No active anomalies detected. Operations normal.
                </div>
            ) : (
                <div className="space-y-4">
                    {anomalies.map((anom) => (
                        <div
                            key={anom.id}
                            className={`p-5 rounded-lg border-l-4 ${getSeverityColor(
                                anom.severity
                            )} shadow-md transition-all hover:brightness-110`}
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="rounded-full bg-black/20 p-2">
                                        {anom.severity === "high" ? "🔴" : "🟡"}
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold">
                                            {anom.severity.toUpperCase()} - {anom.building_id}
                                        </h3>
                                        <p className="text-sm opacity-80 font-mono">
                                            {format(new Date(anom.timestamp), "MMM dd, hh:mm a")}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-2xl font-black">
                                        {anom.deviation_percent.toFixed(0)}%
                                    </div>
                                    <div className="text-xs opacity-75 uppercase tracking-wider">
                                        Deviation
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 bg-black/20 rounded p-4">
                                <div>
                                    <div className="text-sm font-semibold opacity-90 mb-1">Details</div>
                                    <ul className="text-sm space-y-1 opacity-80">
                                        <li>
                                            <strong>Expected:</strong> {anom.expected.toFixed(1)} kWh
                                        </li>
                                        <li>
                                            <strong>Actual:</strong> {(anom.expected + anom.deviation).toFixed(1)} kWh
                                        </li>
                                        <li>
                                            <strong>Flag Type:</strong> {getAnomalyTypeLabel(anom.anomaly_type)}
                                        </li>
                                    </ul>
                                </div>

                                {anom.shap_values && anom.shap_values.length > 0 && (
                                    <div>
                                        <div className="text-sm font-semibold opacity-90 mb-1 flex items-center gap-2">
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                            </svg>
                                            SHAP Leading Factors
                                        </div>
                                        <ul className="text-sm space-y-1 font-mono opacity-80 backdrop-blur-sm">
                                            {anom.shap_values.map((f, i) => (
                                                <li key={i}>• {f}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>

                            {anom.similar_past && anom.similar_past.length > 0 && (
                                <div className="mt-4 border-t border-white/20 pt-4">
                                    <div className="text-sm font-bold opacity-90 mb-2">📋 SIMILAR PAST EVENTS (RAG)</div>
                                    <div className="space-y-2">
                                        {anom.similar_past.map((sp, idx) => (
                                            <div key={idx} className="bg-black/30 rounded p-2 text-sm flex justify-between items-center">
                                                <span className="opacity-80">• {sp.date}: {sp.cause}</span>
                                                <span className="text-xs bg-white/10 px-2 py-1 rounded">{sp.resolution}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-3 mt-5">
                                <button
                                    onClick={() => setAnomalies(anomalies.filter(a => a.id !== anom.id))}
                                    className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded text-sm font-medium transition-colors cursor-pointer"
                                >
                                    Acknowledge
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AnomalyAlertPanel;
