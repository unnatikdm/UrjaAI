import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import Header from '../components/Header'
import { getBuildings, getForecast } from '../services/api'
import { generateBillingPDF } from '../utils/billingPDF'

/* ── Billing periods with multipliers ── */
const PERIODS = [
    { id: 'weekly',     label: 'Weekly',       days: 7,    icon: '📅' },
    { id: 'monthly',    label: 'Monthly',      days: 30,   icon: '🗓️' },
    { id: 'quarterly',  label: 'Quarterly',    days: 90,   icon: '📊' },
    { id: 'halfyear',   label: 'Half-Yearly',  days: 182,  icon: '📆' },
    { id: 'annual',     label: 'Annually',     days: 365,  icon: '🗃️' },
]

/* ── Tariff slabs (Indian commercial rates) ── */
const TARIFF_SLABS = [
    { upTo: 100,    rate: 5.50, label: '0 – 100 kWh' },
    { upTo: 300,    rate: 7.00, label: '101 – 300 kWh' },
    { upTo: 500,    rate: 8.50, label: '301 – 500 kWh' },
    { upTo: Infinity, rate: 10.00, label: '500+ kWh' },
]

const FIXED_CHARGES = {
    weekly: 50,
    monthly: 200,
    quarterly: 550,
    halfyear: 1050,
    annual: 2000,
}

const TAXES = { gst: 0.18, cess: 0.01 }

const PIE_COLORS = ['#16a34a', '#22c55e', '#65a30d', '#eab308', '#f97316', '#ef4444', '#8b5cf6']

function formatCurrency(amount) {
    return '₹' + amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatName(id) {
    return id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function calculateSlabCost(totalKwh) {
    let remaining = totalKwh
    let cost = 0
    let breakdown = []
    let prevLimit = 0

    for (const slab of TARIFF_SLABS) {
        const slabWidth = slab.upTo === Infinity ? remaining : slab.upTo - prevLimit
        const consumed = Math.min(remaining, slabWidth)
        if (consumed <= 0) break
        const slabCost = consumed * slab.rate
        cost += slabCost
        breakdown.push({ label: slab.label, units: consumed, rate: slab.rate, cost: slabCost })
        remaining -= consumed
        prevLimit = slab.upTo
    }
    return { cost, breakdown }
}

/* ── Custom tooltip for bar chart ── */
function BarTooltip({ active, payload }) {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
        <div className="bg-white border border-border rounded-xl p-3 text-xs shadow-xl">
            <p className="font-semibold text-ink-base mb-1">{d.name}</p>
            <p className="text-ink-muted">Consumption: <strong>{d.kwh.toFixed(1)} kWh</strong></p>
            <p className="text-ink-muted">Cost: <strong>{formatCurrency(d.cost)}</strong></p>
        </div>
    )
}

export default function Billing() {
    const navigate = useNavigate()
    const [period, setPeriod] = useState('monthly')
    const [buildings, setBuildings] = useState([])
    const [forecasts, setForecasts] = useState({})
    const [loading, setLoading] = useState(true)

    /* Load buildings and all forecasts */
    useEffect(() => {
        async function load() {
            setLoading(true)
            try {
                const bldgs = await getBuildings()
                setBuildings(bldgs)

                const fcs = {}
                await Promise.all(
                    bldgs.map(async (b) => {
                        try {
                            const fc = await getForecast(b)
                            fcs[b] = fc
                        } catch {
                            fcs[b] = null
                        }
                    })
                )
                setForecasts(fcs)
            } catch (e) {
                console.error('Failed to load billing data:', e)
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [])

    const selectedPeriod = PERIODS.find(p => p.id === period) || PERIODS[1]

    /* Compute per-building billing */
    const billingData = useMemo(() => {
        return buildings.map(b => {
            const fc = forecasts[b]
            // Sum 24h forecast → daily avg, then scale to period
            const dailyKwh = fc
                ? fc.forecast.reduce((s, p) => s + p.consumption, 0)
                : (80 + Math.random() * 120) // fallback simulated
            const periodKwh = dailyKwh * selectedPeriod.days
            const { cost, breakdown } = calculateSlabCost(periodKwh)
            return {
                id: b,
                name: formatName(b),
                kwh: periodKwh,
                cost,
                dailyAvg: dailyKwh,
                breakdown,
            }
        })
    }, [buildings, forecasts, selectedPeriod])

    /* Totals */
    const totals = useMemo(() => {
        const totalKwh = billingData.reduce((s, b) => s + b.kwh, 0)
        const { cost: energyCost, breakdown } = calculateSlabCost(totalKwh)
        const fixedCharge = FIXED_CHARGES[period]
        const subtotal = energyCost + fixedCharge
        const gst = subtotal * TAXES.gst
        const cess = subtotal * TAXES.cess
        const grandTotal = subtotal + gst + cess

        return { totalKwh, energyCost, fixedCharge, subtotal, gst, cess, grandTotal, breakdown }
    }, [billingData, period])

    /* Chart data */
    const barData = billingData.map(b => ({
        name: b.name,
        kwh: b.kwh,
        cost: b.cost,
    })).sort((a, b) => b.kwh - a.kwh)

    const pieData = billingData.map(b => ({
        name: b.name,
        value: Math.round(b.kwh),
    }))

    /* Period date range */
    const endDate = new Date()
    const startDate = new Date(endDate.getTime() - selectedPeriod.days * 86400000)
    const dateRange = `${startDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} — ${endDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}`

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col">
                <Header />
                <main className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <div className="w-12 h-12 mx-auto mb-4 rounded-full border-4 border-green-200 border-t-green-600 animate-spin" />
                        <p className="text-ink-muted text-sm">Calculating billing data…</p>
                    </div>
                </main>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex flex-col bg-surface-sunken">
            <Header />

            <main className="flex-1 px-4 sm:px-6 py-6 max-w-[1600px] mx-auto w-full">
                {/* ── Page header ── */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <button onClick={() => navigate('/')}
                                className="text-ink-lighter hover:text-ink-base transition-colors">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                                </svg>
                            </button>
                            <h1 className="text-2xl font-bold text-ink-base">⚡ Energy Billing</h1>
                        </div>
                        <p className="text-sm text-ink-muted ml-8">{dateRange}</p>
                    </div>

                    {/* Period selector + download */}
                    <div className="flex items-center gap-3">
                        <div className="flex bg-white rounded-xl border border-border-subtle shadow-sm overflow-hidden">
                            {PERIODS.map(p => (
                                <button
                                    key={p.id}
                                    onClick={() => setPeriod(p.id)}
                                    className={`px-4 py-2.5 text-sm font-medium transition-all whitespace-nowrap
                                        ${period === p.id
                                            ? 'bg-green-600 text-white shadow-inner'
                                            : 'text-ink-muted hover:bg-surface-sunken hover:text-ink-base'
                                        }`}
                                >
                                    <span className="hidden sm:inline mr-1.5">{p.icon}</span>
                                    {p.label}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={() => generateBillingPDF({ billingData, totals, selectedPeriod, dateRange, period })}
                            className="flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-xl shadow-sm hover:shadow-md transition-all"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Download PDF
                        </button>
                    </div>
                </div>

                {/* ── Summary cards ── */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="card p-5">
                        <p className="text-[10px] uppercase tracking-wider text-ink-lighter font-medium">Total Consumption</p>
                        <p className="text-2xl font-bold text-ink-base mt-1">{totals.totalKwh.toFixed(0)}<span className="text-sm font-normal text-ink-lighter ml-1">kWh</span></p>
                        <p className="text-xs text-ink-faint mt-1">{selectedPeriod.label} usage across {buildings.length} buildings</p>
                    </div>
                    <div className="card p-5">
                        <p className="text-[10px] uppercase tracking-wider text-ink-lighter font-medium">Energy Charges</p>
                        <p className="text-2xl font-bold text-green-700 mt-1">{formatCurrency(totals.energyCost)}</p>
                        <p className="text-xs text-ink-faint mt-1">Slab-based tariff calculation</p>
                    </div>
                    <div className="card p-5">
                        <p className="text-[10px] uppercase tracking-wider text-ink-lighter font-medium">Taxes & Duties</p>
                        <p className="text-2xl font-bold text-amber-600 mt-1">{formatCurrency(totals.gst + totals.cess)}</p>
                        <p className="text-xs text-ink-faint mt-1">GST 18% + Energy Cess 1%</p>
                    </div>
                    <div className="card p-5 border-2 border-green-200 bg-green-50/50">
                        <p className="text-[10px] uppercase tracking-wider text-green-700 font-medium">Grand Total</p>
                        <p className="text-2xl font-bold text-green-800 mt-1">{formatCurrency(totals.grandTotal)}</p>
                        <p className="text-xs text-green-600 mt-1">Payable for {selectedPeriod.label.toLowerCase()} period</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
                    {/* ── Bar chart: per-building cost ── */}
                    <div className="xl:col-span-2 card p-6">
                        <h3 className="section-title">Building-wise Cost Breakdown</h3>
                        <ResponsiveContainer width="100%" height={320}>
                            <BarChart data={barData} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e8f5ea" vertical={false} />
                                <XAxis dataKey="name" tick={{ fill: '#9cb89e', fontSize: 11 }} axisLine={false} tickLine={false} interval={0}
                                    angle={-20} textAnchor="end" height={60} />
                                <YAxis tick={{ fill: '#9cb89e', fontSize: 11 }} axisLine={false} tickLine={false}
                                    tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
                                <Tooltip content={<BarTooltip />} />
                                <Bar dataKey="cost" radius={[6, 6, 0, 0]} maxBarSize={48}>
                                    {barData.map((_, i) => (
                                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* ── Pie chart: consumption share ── */}
                    <div className="card p-6">
                        <h3 className="section-title">Consumption Share</h3>
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                                    dataKey="value" paddingAngle={3} strokeWidth={0}>
                                    {pieData.map((_, i) => (
                                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip formatter={(v) => `${v} kWh`} />
                                <Legend wrapperStyle={{ fontSize: '11px' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* ── Invoice-style detailed breakdown ── */}
                <div className="card p-6 mb-6">
                    <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                        <h3 className="section-title mb-0">📄 Detailed Bill Statement</h3>
                        <span className="text-xs text-ink-faint bg-surface-sunken px-3 py-1 rounded-full">
                            Invoice #{new Date().getFullYear()}-{String(new Date().getMonth() + 1).padStart(2, '0')}-URJA
                        </span>
                    </div>

                    {/* Building rows */}
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b-2 border-border-default text-left">
                                    <th className="pb-3 text-[10px] uppercase tracking-wider text-ink-lighter font-semibold">#</th>
                                    <th className="pb-3 text-[10px] uppercase tracking-wider text-ink-lighter font-semibold">Building</th>
                                    <th className="pb-3 text-[10px] uppercase tracking-wider text-ink-lighter font-semibold text-right">Daily Avg (kWh)</th>
                                    <th className="pb-3 text-[10px] uppercase tracking-wider text-ink-lighter font-semibold text-right">{selectedPeriod.label} (kWh)</th>
                                    <th className="pb-3 text-[10px] uppercase tracking-wider text-ink-lighter font-semibold text-right">Energy Charges</th>
                                    <th className="pb-3 text-[10px] uppercase tracking-wider text-ink-lighter font-semibold text-right">Share</th>
                                </tr>
                            </thead>
                            <tbody>
                                {billingData.map((b, i) => {
                                    const pct = totals.totalKwh > 0 ? (b.kwh / totals.totalKwh * 100) : 0
                                    return (
                                        <tr key={b.id} className="border-b border-border-subtle hover:bg-surface-sunken/50 transition-colors">
                                            <td className="py-3 text-ink-faint">{i + 1}</td>
                                            <td className="py-3 font-medium text-ink-base">{b.name}</td>
                                            <td className="py-3 text-right tabular-nums text-ink-muted">{b.dailyAvg.toFixed(1)}</td>
                                            <td className="py-3 text-right tabular-nums text-ink-muted">{b.kwh.toFixed(0)}</td>
                                            <td className="py-3 text-right tabular-nums font-semibold text-ink-base">{formatCurrency(b.cost)}</td>
                                            <td className="py-3 text-right">
                                                <div className="inline-flex items-center gap-2">
                                                    <div className="w-16 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                                                        <div className="h-full rounded-full bg-green-500" style={{ width: `${pct}%` }} />
                                                    </div>
                                                    <span className="text-xs text-ink-faint tabular-nums w-10 text-right">{pct.toFixed(1)}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>

                    {/* Totals section */}
                    <div className="mt-6 border-t-2 border-border-default pt-4 max-w-md ml-auto">
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between text-ink-muted">
                                <span>Energy Charges ({totals.totalKwh.toFixed(0)} kWh)</span>
                                <span className="tabular-nums font-medium">{formatCurrency(totals.energyCost)}</span>
                            </div>
                            <div className="flex justify-between text-ink-muted">
                                <span>Fixed / Demand Charges</span>
                                <span className="tabular-nums font-medium">{formatCurrency(totals.fixedCharge)}</span>
                            </div>
                            <div className="border-t border-border-subtle my-2" />
                            <div className="flex justify-between text-ink-muted">
                                <span>Subtotal</span>
                                <span className="tabular-nums font-medium">{formatCurrency(totals.subtotal)}</span>
                            </div>
                            <div className="flex justify-between text-ink-faint text-xs">
                                <span>GST (18%)</span>
                                <span className="tabular-nums">{formatCurrency(totals.gst)}</span>
                            </div>
                            <div className="flex justify-between text-ink-faint text-xs">
                                <span>Energy Cess (1%)</span>
                                <span className="tabular-nums">{formatCurrency(totals.cess)}</span>
                            </div>
                            <div className="border-t-2 border-green-300 my-2" />
                            <div className="flex justify-between text-lg font-bold text-green-800">
                                <span>Grand Total</span>
                                <span className="tabular-nums">{formatCurrency(totals.grandTotal)}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Tariff slabs reference ── */}
                <div className="card p-6">
                    <h3 className="section-title">📋 Tariff Schedule (Commercial)</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                        {TARIFF_SLABS.map((slab, i) => (
                            <div key={i} className="bg-surface-sunken rounded-xl p-4 border border-border-subtle">
                                <p className="text-xs text-ink-lighter font-medium mb-1">Slab {i + 1}</p>
                                <p className="font-semibold text-ink-base text-sm">{slab.label}</p>
                                <p className="text-xl font-bold text-green-700 mt-1">₹{slab.rate.toFixed(2)}<span className="text-xs font-normal text-ink-lighter">/kWh</span></p>
                            </div>
                        ))}
                    </div>
                    <p className="text-[10px] text-ink-faint mt-3">
                        * Rates are indicative and based on standard Indian commercial electricity tariffs. Actual rates may vary by state and utility provider.
                    </p>
                </div>
            </main>

            <footer className="text-center text-xs text-ink-faint py-4 border-t border-border-subtle bg-white">
                Urja AI · Campus Energy Optimization System · {new Date().getFullYear()}
            </footer>
        </div>
    )
}
