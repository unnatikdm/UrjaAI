import { useState, useMemo, useRef, useCallback, useEffect } from 'react'

/* ──────────────────────────────────────────────
   Simulated room-level energy data
   ────────────────────────────────────────────── */
const ROOM_DATA = [
  {
    id: 'lecture-hall-a', name: 'Lecture Hall A', type: 'Lecture Hall', floor: 'Ground Floor',
    consumption: 42.5, capacity: 60, trend: 'up', status: 'high', occupancy: 85,
    recommendations: [
      'Dim lighting to 70 % — natural light is sufficient until 4 PM',
      'Reduce HVAC setpoint by 1 °C during afternoon lectures',
      'Schedule projector auto-off between lecture slots',
    ],
  },
  {
    id: 'lecture-hall-b', name: 'Lecture Hall B', type: 'Lecture Hall', floor: 'Ground Floor',
    consumption: 18.3, capacity: 60, trend: 'down', status: 'low', occupancy: 30,
    recommendations: [
      'Current usage is optimal — no action needed',
      'Consider consolidating classes to this hall during off-peak',
    ],
  },
  {
    id: 'computer-lab', name: 'Computer Lab', type: 'Lab', floor: 'First Floor',
    consumption: 35.7, capacity: 40, trend: 'up', status: 'medium', occupancy: 72,
    recommendations: [
      'Enable sleep mode on idle workstations after 10 min',
      'Switch to LED panel lighting (saves ~15 %)',
      'Stagger AC zones — cool occupied areas first',
    ],
  },
  {
    id: 'library', name: 'Central Library', type: 'Library', floor: 'Ground Floor',
    consumption: 28.1, capacity: 45, trend: 'stable', status: 'medium', occupancy: 55,
    recommendations: [
      'Install occupancy sensors for zone-based lighting',
      'Reduce after-hours lighting to emergency-only mode',
    ],
  },
  {
    id: 'admin-office', name: 'Admin Office', type: 'Office', floor: 'First Floor',
    consumption: 12.4, capacity: 20, trend: 'down', status: 'low', occupancy: 40,
    recommendations: [
      'Usage is within efficient range',
      'Consider smart power strips for desk equipment',
    ],
  },
  {
    id: 'cafeteria', name: 'Cafeteria', type: 'Dining', floor: 'Ground Floor',
    consumption: 38.9, capacity: 50, trend: 'up', status: 'high', occupancy: 90,
    recommendations: [
      'Switch to induction cooking (30 % more energy efficient)',
      'Install timer-controlled ventilation for exhaust fans',
      'Use waste heat from kitchen for water pre-heating',
    ],
  },
  {
    id: 'server-room', name: 'Server Room', type: 'Infrastructure', floor: 'Basement',
    consumption: 55.2, capacity: 70, trend: 'stable', status: 'critical', occupancy: 100,
    recommendations: [
      'Implement hot/cold aisle containment to reduce cooling by 20 %',
      'Migrate low-priority workloads to cloud during peak campus hours',
      'Install blanking panels in empty rack spaces',
      'Upgrade to variable-speed cooling fans',
    ],
  },
  {
    id: 'common-area', name: 'Main Lobby', type: 'Common Area', floor: 'Ground Floor',
    consumption: 15.6, capacity: 25, trend: 'down', status: 'low', occupancy: 20,
    recommendations: [
      'Daylight harvesting sensors can cut lighting by 40 %',
      'Current consumption is below average — well managed',
    ],
  },
]

/* ──────────────────────────────────────────────
   Room layout (world coordinates)
   Centre of campus ≈ (285, 200) used as pivot
   ────────────────────────────────────────────── */
const CAMPUS_CX = 285
const CAMPUS_CY = 200

const ISO_ROOMS = {
  'lecture-hall-a': { x: 110, y: 110, w: 100, d: 55, h: 38 },
  'library':        { x: 230, y: 110, w: 110, d: 55, h: 32 },
  'lecture-hall-b': { x: 360, y: 110, w: 100, d: 55, h: 34 },
  'computer-lab':   { x: 110, y: 200, w: 100, d: 45, h: 26 },
  'common-area':    { x: 230, y: 200, w: 110, d: 45, h: 12 },
  'admin-office':   { x: 360, y: 200, w: 100, d: 45, h: 20 },
  'cafeteria':      { x: 110, y: 285, w: 100, d: 45, h: 28 },
  'server-room':    { x: 360, y: 285, w: 100, d: 45, h: 40 },
}

const STATUS_COLORS = {
  low:      { top: '#22c55e', left: '#16a34a', right: '#15803d', badge: 'bg-green-100 text-green-700',  label: 'Efficient' },
  medium:   { top: '#eab308', left: '#ca8a04', right: '#a16207', badge: 'bg-amber-100 text-amber-700',  label: 'Moderate' },
  high:     { top: '#ef4444', left: '#dc2626', right: '#b91c1c', badge: 'bg-red-100 text-red-700',      label: 'High Usage' },
  critical: { top: '#f43f5e', left: '#e11d48', right: '#be123c', badge: 'bg-rose-100 text-rose-700',    label: 'Critical' },
}

const TREND_ICONS = { up: '↗', down: '↘', stable: '→' }

/* ──────────────────────────────────────────────
   Isometric projection WITH rotation.
   Steps:
   1. Translate so campus centre is at origin
   2. Rotate world coords by θ on XY plane
   3. Apply standard isometric projection
   ────────────────────────────────────────────── */
const COS30 = Math.cos(Math.PI / 6)

function toIso(x, y, rotRad) {
  // Rotate around campus centre
  const dx = x - CAMPUS_CX
  const dy = y - CAMPUS_CY
  const rx = dx * Math.cos(rotRad) - dy * Math.sin(rotRad) + CAMPUS_CX
  const ry = dx * Math.sin(rotRad) + dy * Math.cos(rotRad) + CAMPUS_CY
  // Standard isometric
  return [(rx - ry) * COS30, (rx + ry) * 0.25]
}

function isoBlock(gx, gy, w, d, h, rot) {
  // Get the 4 corners of the footprint
  const corners = [
    [gx, gy],
    [gx + w, gy],
    [gx + w, gy + d],
    [gx, gy + d],
  ]
  const projected = corners.map(([cx, cy]) => toIso(cx, cy, rot))

  // For the 3D block we need:
  // - 4 top-face vertices (projected - height)
  // - 4 bottom-face vertices (projected)
  const top = projected.map(([px, py]) => [px, py - h])
  const bot = projected

  const topFace = top.map(p => p.join(',')).join(' ')

  // We draw walls for the 4 edges, but only the ones facing the camera
  // (the ones whose bottom midpoint is lower on screen = more "in front")
  // Build all 4 walls, then pick the 2 with highest screen-y
  const walls = []
  for (let i = 0; i < 4; i++) {
    const j = (i + 1) % 4
    const midY = (bot[i][1] + bot[j][1]) / 2
    walls.push({
      idx: i,
      midY,
      points: `${top[i].join(',')
        } ${top[j].join(',')
        } ${bot[j].join(',')
        } ${bot[i].join(',')}`
    })
  }
  // Sort so the 2 with highest midY are the "front" — they face camera
  walls.sort((a, b) => b.midY - a.midY)

  const cx = (projected[0][0] + projected[1][0] + projected[2][0] + projected[3][0]) / 4
  const cy = (projected[0][1] + projected[1][1] + projected[2][1] + projected[3][1]) / 4 - h

  const groundFace = bot.map(p => p.join(',')).join(' ')

  return { topFace, walls, cx, cy, groundFace, top, bot, projected }
}

/* ── Decorations ── */
function IsoTree({ x, y, scale = 1, rot }) {
  const [bx, by] = toIso(x, y, rot)
  const s = scale
  return (
    <g>
      <line x1={bx} y1={by} x2={bx} y2={by - 10 * s} stroke="#5D4037" strokeWidth={2 * s} />
      <ellipse cx={bx} cy={by - 14 * s} rx={7 * s} ry={5 * s} fill="#2d6a4f" opacity={0.9} />
      <ellipse cx={bx} cy={by - 18 * s} rx={5 * s} ry={4 * s} fill="#40916c" opacity={0.85} />
      <ellipse cx={bx} cy={by - 21 * s} rx={3 * s} ry={3 * s} fill="#52b788" opacity={0.8} />
    </g>
  )
}

function IsoLamp({ x, y, rot }) {
  const [bx, by] = toIso(x, y, rot)
  return (
    <g>
      <line x1={bx} y1={by} x2={bx} y2={by - 14} stroke="#78909C" strokeWidth={1.5} />
      <circle cx={bx} cy={by - 15} r={2.5} fill="#FDD835" opacity={0.9} />
      <circle cx={bx} cy={by - 15} r={6} fill="#FDD835" opacity={0.08} />
    </g>
  )
}

function IsoPath({ points, rot }) {
  const isoPoints = points.map(([x, y]) => toIso(x, y, rot).join(',')).join(' ')
  return <polygon points={isoPoints} fill="rgba(120,144,156,0.12)" stroke="rgba(120,144,156,0.08)" strokeWidth={0.5} />
}

/* ──────────────────────────────────────────────
   Main Component
   ────────────────────────────────────────────── */
export default function CampusBlueprint({ onBuildingSelect }) {
  const [selectedRoom, setSelectedRoom] = useState(null)
  const [hoveredRoom, setHoveredRoom] = useState(null)

  /* View state: pan, zoom, rotation */
  const [view, setView] = useState({ panX: 0, panY: 0, zoom: 1, rotation: 0 })
  const containerRef = useRef(null)
  const dragRef = useRef(null)

  const rotRad = (view.rotation * Math.PI) / 180

  /* ── Scroll to zoom ── */
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const handle = (e) => {
      e.preventDefault()
      setView(prev => {
        const factor = e.deltaY > 0 ? 0.92 : 1.08
        return { ...prev, zoom: Math.max(0.35, Math.min(3.5, prev.zoom * factor)) }
      })
    }
    el.addEventListener('wheel', handle, { passive: false })
    return () => el.removeEventListener('wheel', handle)
  }, [])

  /* ── Mouse drag: normal = pan, Shift = rotate ── */
  const onMouseDown = useCallback((e) => {
    if (e.button !== 0) return
    if (e.target.closest('[data-building]')) return
    dragRef.current = {
      startX: e.clientX, startY: e.clientY,
      startPanX: view.panX, startPanY: view.panY,
      startRotation: view.rotation,
      mode: e.shiftKey ? 'rotate' : 'pan',
    }
  }, [view.panX, view.panY, view.rotation])

  const onMouseMove = useCallback((e) => {
    if (!dragRef.current) return
    const dx = e.clientX - dragRef.current.startX
    const dy = e.clientY - dragRef.current.startY

    if (dragRef.current.mode === 'rotate') {
      setView(prev => ({
        ...prev,
        rotation: (dragRef.current.startRotation + dx * 0.5) % 360,
      }))
    } else {
      setView(prev => ({
        ...prev,
        panX: dragRef.current.startPanX + dx / prev.zoom,
        panY: dragRef.current.startPanY + dy / prev.zoom,
      }))
    }
  }, [])

  const onMouseUp = useCallback(() => { dragRef.current = null }, [])

  useEffect(() => {
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [onMouseMove, onMouseUp])

  const resetView = () => setView({ panX: 0, panY: 0, zoom: 1, rotation: 0 })
  const zoomIn = () => setView(p => ({ ...p, zoom: Math.min(3.5, p.zoom * 1.3) }))
  const zoomOut = () => setView(p => ({ ...p, zoom: Math.max(0.35, p.zoom * 0.75) }))
  const rotateLeft = () => setView(p => ({ ...p, rotation: (p.rotation - 45) % 360 }))
  const rotateRight = () => setView(p => ({ ...p, rotation: (p.rotation + 45) % 360 }))

  const totalConsumption = useMemo(
    () => ROOM_DATA.reduce((sum, r) => sum + r.consumption, 0).toFixed(1), []
  )

  const selectedData = useMemo(
    () => ROOM_DATA.find(r => r.id === selectedRoom), [selectedRoom]
  )

  /* Sort buildings by depth for correct draw order.
     Depth depends on rotation — buildings further from camera draw first. */
  const sortedRooms = useMemo(() =>
    ROOM_DATA.slice().sort((a, b) => {
      const ga = ISO_ROOMS[a.id]; const gb = ISO_ROOMS[b.id]
      // Centre of each building in world coords
      const acx = ga.x + ga.w / 2, acy = ga.y + ga.d / 2
      const bcx = gb.x + gb.w / 2, bcy = gb.y + gb.d / 2
      // After rotation, which is "further back" on screen?
      const [, ay] = toIso(acx, acy, rotRad)
      const [, by_] = toIso(bcx, bcy, rotRad)
      return ay - by_ // Draw lower screen-y first (further from viewer)
    }), [rotRad]
  )

  const isModified = view.zoom !== 1 || view.panX !== 0 || view.panY !== 0 || view.rotation !== 0

  /* ── Compass needle angle — it should counter-rotate to show real North ── */
  const compassAngle = -view.rotation

  return (
    <section className="bg-white rounded-xl border border-border-subtle shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-border-subtle flex items-center gap-2 flex-wrap">
        <span className="text-lg">🏛️</span>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-brand-primary">Campus Blueprint</h2>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-[10px] text-ink-lighter bg-surface-sunken px-2 py-1 rounded hidden sm:inline">
            Drag = pan · Shift+Drag = rotate · Scroll = zoom
          </span>
          <span className="text-xs text-ink-lighter">Total: <strong>{totalConsumption} kWh</strong></span>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        {/* ═══ SVG Map ═══ */}
        <div className={`relative transition-all duration-300 ${selectedRoom ? 'lg:w-3/5' : 'w-full'}`}>

          {/* Zoom & Rotate buttons */}
          <div className="absolute top-3 right-3 z-10 flex flex-col gap-1.5">
            <button onClick={zoomIn} title="Zoom in"
              className="w-9 h-9 rounded-lg bg-slate-800/90 hover:bg-slate-600 text-white flex items-center justify-center text-lg font-bold backdrop-blur-md border border-slate-500/40 transition-colors shadow-lg">+</button>
            <button onClick={zoomOut} title="Zoom out"
              className="w-9 h-9 rounded-lg bg-slate-800/90 hover:bg-slate-600 text-white flex items-center justify-center text-lg font-bold backdrop-blur-md border border-slate-500/40 transition-colors shadow-lg">−</button>
            <div className="w-9 h-[1px] bg-slate-600/30 my-0.5" />
            <button onClick={rotateLeft} title="Rotate left 45°"
              className="w-9 h-9 rounded-lg bg-slate-800/90 hover:bg-slate-600 text-white flex items-center justify-center text-base backdrop-blur-md border border-slate-500/40 transition-colors shadow-lg">↺</button>
            <button onClick={rotateRight} title="Rotate right 45°"
              className="w-9 h-9 rounded-lg bg-slate-800/90 hover:bg-slate-600 text-white flex items-center justify-center text-base backdrop-blur-md border border-slate-500/40 transition-colors shadow-lg">↻</button>
            {isModified && (
              <>
                <div className="w-9 h-[1px] bg-slate-600/30 my-0.5" />
                <button onClick={resetView} title="Reset view"
                  className="w-9 h-9 rounded-lg bg-slate-800/90 hover:bg-slate-600 text-white flex items-center justify-center text-sm backdrop-blur-md border border-slate-500/40 transition-colors shadow-lg">⟲</button>
              </>
            )}
          </div>

          {/* Info badge */}
          {isModified && (
            <div className="absolute bottom-3 left-3 z-10 flex items-center gap-2">
              <span className="text-[10px] text-slate-400 bg-slate-900/70 px-2 py-1 rounded backdrop-blur-sm">
                {Math.round(view.zoom * 100)}%
              </span>
              {view.rotation !== 0 && (
                <span className="text-[10px] text-slate-400 bg-slate-900/70 px-2 py-1 rounded backdrop-blur-sm">
                  {Math.round(view.rotation)}°
                </span>
              )}
            </div>
          )}

          <div
            ref={containerRef}
            className="overflow-hidden"
            style={{ cursor: dragRef.current ? 'grabbing' : 'grab' }}
            onMouseDown={onMouseDown}
          >
            <svg
              viewBox="-340 -60 680 380"
              className="w-full select-none"
              style={{
                background: 'linear-gradient(170deg, #0a0f1e 0%, #111827 40%, #0f172a 100%)',
                aspectRatio: '16/9',
              }}
              preserveAspectRatio="xMidYMid meet"
            >
              <defs>
                <pattern id="campusGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(100,116,139,0.04)" strokeWidth="0.3" />
                </pattern>
                <filter id="bldgGlow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
                <filter id="groundShadow"><feGaussianBlur stdDeviation="2" /></filter>
                <radialGradient id="grassGlow1" cx="30%" cy="40%">
                  <stop offset="0%" stopColor="rgba(34,197,94,0.06)" />
                  <stop offset="100%" stopColor="transparent" />
                </radialGradient>
              </defs>

              {/* Pan + Zoom wrapper (rotation is baked into the projection math) */}
              <g transform={`translate(${view.panX}, ${view.panY}) scale(${view.zoom})`}
                 style={{ transformOrigin: '0px 100px' }}>

                <rect x="-500" y="-200" width="1000" height="600" fill="url(#campusGrid)" />
                <rect x="-500" y="-200" width="1000" height="600" fill="url(#grassGlow1)" />

                <text x="0" y="-30" textAnchor="middle" fill="rgba(148,163,184,0.35)" fontSize="7" fontFamily="monospace" letterSpacing="5">
                  URJA AI · CAMPUS ENERGY MAP
                </text>

                {/* Ground */}
                <IsoPath points={[[70, 80], [500, 80], [500, 370], [70, 370]]} rot={rotRad} />
                {/* Paths */}
                <IsoPath points={[[260, 370], [320, 370], [320, 415], [260, 415]]} rot={rotRad} />
                <IsoPath points={[[500, 210], [540, 210], [540, 270], [500, 270]]} rot={rotRad} />
                <IsoPath points={[[30, 210], [70, 210], [70, 270], [30, 270]]} rot={rotRad} />
                <IsoPath points={[[255, 200], [325, 200], [325, 285], [255, 285]]} rot={rotRad} />

                {/* Trees */}
                <IsoTree x={80} y={90} scale={0.75} rot={rotRad} />
                <IsoTree x={490} y={90} scale={0.7} rot={rotRad} />
                <IsoTree x={285} y={85} scale={0.8} rot={rotRad} />
                <IsoTree x={270} y={350} scale={0.85} rot={rotRad} />
                <IsoTree x={320} y={355} scale={0.7} rot={rotRad} />
                <IsoTree x={50} y={190} scale={0.6} rot={rotRad} />
                <IsoTree x={50} y={310} scale={0.65} rot={rotRad} />
                <IsoTree x={525} y={190} scale={0.6} rot={rotRad} />
                <IsoTree x={525} y={310} scale={0.65} rot={rotRad} />

                {/* Lamps */}
                <IsoLamp x={260} y={390} rot={rotRad} />
                <IsoLamp x={320} y={390} rot={rotRad} />
                <IsoLamp x={535} y={240} rot={rotRad} />
                <IsoLamp x={45} y={240} rot={rotRad} />

                {/* ── Buildings (sorted by depth for correct draw order) ── */}
                {sortedRooms.map(room => {
                  const geo = ISO_ROOMS[room.id]
                  if (!geo) return null
                  const colors = STATUS_COLORS[room.status]
                  const block = isoBlock(geo.x, geo.y, geo.w, geo.d, geo.h, rotRad)
                  const isHovered = hoveredRoom === room.id
                  const isSelected = selectedRoom === room.id

                  return (
                    <g key={room.id} data-building={room.id} className="cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation()
                        const newRoom = selectedRoom === room.id ? null : room.id
                        setSelectedRoom(newRoom)
                        if (newRoom && onBuildingSelect) onBuildingSelect(newRoom)
                      }}
                      onMouseEnter={() => setHoveredRoom(room.id)}
                      onMouseLeave={() => setHoveredRoom(null)}
                      filter={isHovered || isSelected ? 'url(#bldgGlow)' : undefined}>

                      {/* Ground shadow */}
                      <polygon points={block.groundFace} fill="rgba(0,0,0,0.18)" filter="url(#groundShadow)" />

                      {/* Walls — draw all 4, the sort makes back walls draw first (occluded by front) */}
                      {block.walls.map((wall, wi) => {
                        // The first 2 in the sorted list have highest midY → they face the camera
                        const isFront = wi < 2
                        return (
                          <polygon key={wi} points={wall.points}
                            fill={isFront ? colors.left : colors.right}
                            stroke="rgba(0,0,0,0.25)" strokeWidth="0.4"
                            opacity={isHovered ? 0.95 : (isFront ? 0.82 : 0.7)} />
                        )
                      })}

                      {/* Roof */}
                      <polygon points={block.topFace} fill={colors.top}
                        stroke={isSelected ? '#fff' : 'rgba(255,255,255,0.25)'}
                        strokeWidth={isSelected ? 1.5 : 0.4}
                        opacity={isHovered ? 1 : 0.88} />

                      {/* Building label */}
                      <text x={block.cx} y={block.cy - 2} textAnchor="middle" fill="#fff"
                        fontSize={7} fontWeight="700" fontFamily="system-ui, sans-serif"
                        style={{ textShadow: '0 1px 4px rgba(0,0,0,0.7)' }}>
                        {room.name}
                      </text>
                      <text x={block.cx} y={block.cy + 7} textAnchor="middle"
                        fill="rgba(255,255,255,0.85)" fontSize="6" fontWeight="600" fontFamily="monospace">
                        {room.consumption} kWh {TREND_ICONS[room.trend]}
                      </text>

                      {/* Critical pulse */}
                      {room.status === 'critical' && (
                        <polygon points={block.topFace} fill="none" stroke={colors.top} strokeWidth="1.5">
                          <animate attributeName="opacity" values="0.7;0.1;0.7" dur="2s" repeatCount="indefinite" />
                          <animate attributeName="stroke-width" values="1.5;4;1.5" dur="2s" repeatCount="indefinite" />
                        </polygon>
                      )}
                    </g>
                  )
                })}

                {/* Legend */}
                <g transform="translate(190, 250)">
                  <text x={0} y={0} fill="rgba(148,163,184,0.45)" fontSize="6" fontFamily="monospace" letterSpacing="2">ENERGY SCALE</text>
                  {[
                    { label: 'Low', color: STATUS_COLORS.low.top },
                    { label: 'Medium', color: STATUS_COLORS.medium.top },
                    { label: 'High', color: STATUS_COLORS.high.top },
                    { label: 'Critical', color: STATUS_COLORS.critical.top },
                  ].map((item, i) => (
                    <g key={item.label} transform={`translate(0, ${10 + i * 12})`}>
                      <rect x={0} y={0} width={7} height={7} rx={1.5} fill={item.color} opacity={0.9} />
                      <text x={11} y={6.5} fill="rgba(226,232,240,0.6)" fontSize="6.5">{item.label}</text>
                    </g>
                  ))}
                </g>

                {/* Compass with rotation */}
                <g transform="translate(-280, 250)">
                  <circle cx={0} cy={0} r={14} fill="rgba(30,41,59,0.7)" stroke="rgba(100,116,139,0.3)" strokeWidth={0.5} />
                  <g transform={`rotate(${compassAngle})`}>
                    <text x={0} y={-5} textAnchor="middle" fill="rgba(239,68,68,0.7)" fontSize="5" fontWeight="700">N</text>
                    <polygon points="0,-10 -2.5,-5 2.5,-5" fill="rgba(239,68,68,0.6)" />
                    <polygon points="0,10 -2.5,5 2.5,5" fill="rgba(226,232,240,0.25)" />
                    <line x1={0} y1={-3} x2={0} y2={3} stroke="rgba(226,232,240,0.3)" strokeWidth={0.5} />
                  </g>
                  <circle cx={0} cy={0} r={1.5} fill="rgba(226,232,240,0.4)" />
                </g>
              </g>
            </svg>
          </div>
        </div>

        {/* ═══ Detail Panel ═══ */}
        {selectedRoom && selectedData && (
          <div className="lg:w-2/5 border-l border-border-subtle bg-surface-base animate-slideIn overflow-y-auto max-h-[520px]">
            <div className="sticky top-0 bg-white z-10 px-5 py-4 border-b border-border-subtle flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-ink-base text-lg">{selectedData.name}</h3>
                <p className="text-xs text-ink-lighter">{selectedData.type} · {selectedData.floor}</p>
              </div>
              <button onClick={() => setSelectedRoom(null)}
                className="text-ink-lighter hover:text-ink-base transition-colors p-1 rounded-lg hover:bg-surface-sunken">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="px-5 py-4 grid grid-cols-2 gap-3">
              <div className="bg-surface-sunken rounded-lg p-3">
                <p className="text-[10px] uppercase tracking-wider text-ink-lighter font-medium">Consumption</p>
                <p className="text-xl font-bold text-ink-base mt-1">{selectedData.consumption}<span className="text-sm font-normal text-ink-lighter ml-1">kWh</span></p>
              </div>
              <div className="bg-surface-sunken rounded-lg p-3">
                <p className="text-[10px] uppercase tracking-wider text-ink-lighter font-medium">Status</p>
                <span className={`inline-block mt-2 text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_COLORS[selectedData.status].badge}`}>
                  {STATUS_COLORS[selectedData.status].label}
                </span>
              </div>
              <div className="bg-surface-sunken rounded-lg p-3">
                <p className="text-[10px] uppercase tracking-wider text-ink-lighter font-medium">Occupancy</p>
                <p className="text-xl font-bold text-ink-base mt-1">{selectedData.occupancy}<span className="text-sm font-normal text-ink-lighter ml-1">%</span></p>
              </div>
              <div className="bg-surface-sunken rounded-lg p-3">
                <p className="text-[10px] uppercase tracking-wider text-ink-lighter font-medium">Trend</p>
                <p className="text-xl font-bold text-ink-base mt-1">{TREND_ICONS[selectedData.trend]}<span className="text-sm font-normal text-ink-lighter ml-2 capitalize">{selectedData.trend}</span></p>
              </div>
            </div>
            <div className="px-5 pb-3">
              <div className="flex justify-between text-[10px] uppercase tracking-wider text-ink-lighter font-medium mb-1">
                <span>Usage vs Capacity</span><span>{selectedData.consumption} / {selectedData.capacity} kWh</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((selectedData.consumption / selectedData.capacity) * 100, 100)}%`, background: STATUS_COLORS[selectedData.status].top }} />
              </div>
            </div>
            <div className="px-5 py-4 border-t border-border-subtle">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-brand-primary mb-3 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.674M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI Recommendations
              </h4>
              <ul className="space-y-2">
                {selectedData.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-ink-base bg-surface-sunken rounded-lg p-3">
                    <span className="text-brand-primary font-bold mt-0.5 flex-shrink-0">{i + 1}.</span><span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="px-5 py-4 border-t border-border-subtle bg-green-50/50">
              <div className="flex items-center gap-2">
                <span className="text-lg">💡</span>
                <div>
                  <p className="text-xs font-semibold text-green-700">Estimated Savings Potential</p>
                  <p className="text-sm text-green-600">Up to <strong>{(selectedData.consumption * 0.2).toFixed(1)} kWh</strong> (~20 %) by implementing above</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
