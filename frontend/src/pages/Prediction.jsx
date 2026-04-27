import { useState, useEffect, useMemo, useRef } from 'react'
import { Link } from 'react-router-dom'
import { predictionsApi, makesApi, carsApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { HoverPeek } from '../components/ui/link-preview'

const DEFAULTS = {
  make: '', model: '', year: '2019', body_type: 'SUV',
  mileage: '80000', color: 'Negru', fuel_type: 'Diesel',
  engine_capacity: '1995', engine_power: '150',
  gearbox: 'Manuala', transmission: 'Fata', pollution_standard: 'Euro 6',
}

// ── Equipment catalogue ─────────────────────────────────────────────────────
const EQUIPMENT_GROUPS = [
  {
    label: 'Connectivity',
    items: [
      { key: 'apple_carplay',      label: 'Apple CarPlay' },
      { key: 'android_auto',       label: 'Android Auto' },
      { key: 'bluetooth',          label: 'Bluetooth' },
      { key: 'navigation',         label: 'Navigation' },
      { key: 'wireless_charging',  label: 'Wireless Charging' },
      { key: 'usb_port',           label: 'USB Port' },
      { key: 'head_up_display',    label: 'Head-Up Display' },
      { key: 'internet',           label: 'Internet / Wi-Fi' },
    ],
  },
  {
    label: 'Climate & Comfort',
    items: [
      { key: 'ac',               label: 'Air Conditioning' },
      { key: 'climatronic',      label: 'Climatronic (1-zone)' },
      { key: 'climatronic_2zone',label: 'Climatronic 2-zone' },
      { key: 'climatronic_3zone',label: 'Climatronic 3-zone' },
      { key: 'heated_windshield',label: 'Heated Windshield' },
      { key: 'front_armrest',    label: 'Front Armrest' },
    ],
  },
  {
    label: 'Roof',
    items: [
      { key: 'panoramic_roof',     label: 'Panoramic Roof' },
      { key: 'electric_sunroof',   label: 'Electric Sunroof' },
      { key: 'manual_sunroof',     label: 'Manual Sunroof' },
      { key: 'rear_glass_sunroof', label: 'Rear Glass Sunroof' },
    ],
  },
  {
    label: 'Seats & Interior',
    items: [
      { key: 'upholstery_leather',      label: 'Full Leather' },
      { key: 'upholstery_leather_mix',  label: 'Leather Mix' },
      { key: 'upholstery_alcantara',    label: 'Alcantara' },
      { key: 'heated_driver_seat',      label: 'Heated Driver Seat' },
      { key: 'heated_passenger_seat',   label: 'Heated Passenger Seat' },
      { key: 'ventilated_front_seats',  label: 'Ventilated Front Seats' },
      { key: 'ventilated_rear_seats',   label: 'Ventilated Rear Seats' },
      { key: 'electric_driver_seat',    label: 'Electric Driver Seat' },
      { key: 'memory_seat',             label: 'Memory Seat' },
      { key: 'sport_steering_wheel',    label: 'Sport Steering Wheel' },
      { key: 'paddle_shifters',         label: 'Paddle Shifters' },
    ],
  },
  {
    label: 'Driving Assistance',
    items: [
      { key: 'cruise_control',    label: 'Cruise Control' },
      { key: 'adaptive_cruise',   label: 'Adaptive Cruise Control' },
      { key: 'predictive_acc',    label: 'Predictive ACC' },
      { key: 'lane_assist',       label: 'Lane Assist' },
      { key: 'blind_spot',        label: 'Blind Spot Monitor' },
      { key: 'distance_control',  label: 'Distance Control' },
      { key: 'autonomous_driving',label: 'Autonomous Driving' },
      { key: 'keyless_entry',     label: 'Keyless Entry' },
      { key: 'keyless_go',        label: 'Keyless Go (Start)' },
      { key: 'air_suspension',    label: 'Air Suspension' },
      { key: 'sport_suspension',  label: 'Sport Suspension' },
    ],
  },
  {
    label: 'Lighting',
    items: [
      { key: 'led_lights',       label: 'LED Headlights' },
      { key: 'xenon',            label: 'Xenon' },
      { key: 'bi_xenon',         label: 'Bi-Xenon' },
      { key: 'laser_lights',     label: 'Laser Lights' },
      { key: 'dynamic_lights',   label: 'Dynamic Lights' },
      { key: 'follow_me_home',   label: 'Follow-Me-Home' },
    ],
  },
  {
    label: 'Parking & Safety',
    items: [
      { key: 'front_park_sensors', label: 'Front Park Sensors' },
      { key: 'rear_park_sensors',  label: 'Rear Park Sensors' },
      { key: 'park_assist',        label: 'Park Assist' },
      { key: 'auto_park',          label: 'Auto Park' },
      { key: 'rear_camera',        label: 'Rear Camera' },
      { key: 'camera_360',         label: '360° Camera' },
      { key: 'folding_mirrors',    label: 'Folding Mirrors' },
      { key: 'isofix',             label: 'ISOFIX' },
    ],
  },
]

const DEAL_STYLES = {
  'Great Deal':   { bg: 'bg-emerald-100', text: 'text-emerald-800', icon: '▼▼' },
  'Good Deal':    { bg: 'bg-green-100',   text: 'text-green-700',   icon: '▼' },
  'Fair Price':   { bg: 'bg-gray-100',    text: 'text-gray-600',    icon: '—' },
  'Above Market': { bg: 'bg-orange-100',  text: 'text-orange-700',  icon: '▲' },
  'Overpriced':   { bg: 'bg-red-100',     text: 'text-red-700',     icon: '▲▲' },
}

function DealBadge({ score }) {
  if (!score) return <span className="text-[10px] text-as-muted">...</span>
  const style = DEAL_STYLES[score.deal_label] || DEAL_STYLES['Fair Price']
  const sign = score.deal_pct > 0 ? '+' : ''
  return (
    <div className="flex flex-col items-start gap-0.5">
      <span className={`deal-badge inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${style.bg} ${style.text}`}>
        {style.icon} {score.deal_label}
      </span>
      <span className="text-[10px] text-as-muted leading-tight">
        {sign}{score.deal_pct}% vs est. €{Number(score.predicted_price).toLocaleString()}
      </span>
    </div>
  )
}

const ALL_EQUIP_KEYS = EQUIPMENT_GROUPS.flatMap(g => g.items.map(i => i.key))
const EMPTY_EQUIP = Object.fromEntries(ALL_EQUIP_KEYS.map(k => [k, false]))

function equipTier(n) {
  if (n >= 15) return { label: 'Ultra', color: 'text-white bg-black' }
  if (n >= 10) return { label: 'Premium', color: 'text-white bg-as-body' }
  if (n >= 5)  return { label: 'Standard', color: 'text-black bg-as-chip' }
  return { label: 'Basic', color: 'text-as-muted bg-[#f0f0f0]' }
}

function SelectField({ label, name, opts, value, onChange, required }) {
  return (
    <div>
      <label className="block text-xs font-medium text-as-body mb-1">{label}</label>
      <select className="select-field text-sm" value={value} onChange={(e) => onChange(name, e.target.value)} required={required}>
        <option value="">Select...</option>
        {(opts || []).map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )
}

function NumberField({ label, name, placeholder, value, onChange, unit }) {
  return (
    <div>
      <label className="block text-xs font-medium text-as-body mb-1">{label}</label>
      <div className="relative">
        <input type="number" className="input-field text-sm" value={value} placeholder={placeholder}
          onChange={(e) => onChange(name, e.target.value)} required />
        {unit && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-as-muted pointer-events-none">{unit}</span>
        )}
      </div>
    </div>
  )
}

export default function Prediction() {
  const [form, setForm] = useState(DEFAULTS)
  const [equip, setEquip] = useState(EMPTY_EQUIP)
  const [options, setOptions] = useState({})
  const [modelOptions, setModelOptions] = useState(null)
  const [models, setModels] = useState([])
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [recs, setRecs] = useState(null)
  const [recScores, setRecScores] = useState({})
  const [equipValues, setEquipValues] = useState({})
  const [showEquip, setShowEquip] = useState(false)
  const [showRoi, setShowRoi] = useState(false)
  const resultRef = useRef(null)

  useEffect(() => {
    makesApi.options().then((r) => setOptions(r.data)).catch(() => {})
    predictionsApi.equipmentValues().then((r) => setEquipValues(r.data.values || {})).catch(() => {})
    loadHistory()
  }, [])

  useEffect(() => {
    if (form.make) {
      makesApi.models(form.make).then((r) => setModels(r.data.models || [])).catch(() => setModels([]))
    } else {
      setModels([])
    }
  }, [form.make])

  useEffect(() => {
    if (form.make && form.model) {
      makesApi.modelOptions(form.make, form.model).then((r) => {
        const mo = r.data
        setModelOptions(mo)
        setForm((prev) => {
          const updated = { ...prev }
          const checks = [
            ['body_type', 'body_types'], ['fuel_type', 'fuel_types'],
            ['gearbox', 'gearboxes'], ['transmission', 'transmissions'],
            ['pollution_standard', 'pollution_standards'], ['color', 'colors'],
          ]
          for (const [field, key] of checks) {
            if (mo[key] && mo[key].length > 0 && !mo[key].includes(prev[field])) {
              updated[field] = mo[key].length === 1 ? mo[key][0] : ''
            }
          }
          return updated
        })
      }).catch(() => setModelOptions(null))
    } else {
      setModelOptions(null)
    }
  }, [form.make, form.model])

  useEffect(() => {
    if (!result) return
    setRecs(null)
    carsApi.recommendations({
      make: result.input.make, model: result.input.model,
      year: result.input.year, mileage: result.input.mileage,
      predicted_price: result.predicted_price, limit: 5,
    }).then((r) => setRecs(r.data)).catch(() => setRecs([]))
  }, [result])

  useEffect(() => {
    if (!recs || recs.length === 0) { setRecScores({}); return }
    carsApi.dealScores(recs.map((c) => c.id))
      .then((res) => {
        const map = {}
        for (const s of res.data.scores) map[s.car_id] = s
        setRecScores(map)
      })
      .catch(() => setRecScores({}))
  }, [recs])

  const { user } = useAuth()

  const loadHistory = () => {
    predictionsApi.history({ limit: 10 }).then((r) => setHistory(r.data)).catch(() => {})
  }

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))
  const toggleEquip = (k) => setEquip((p) => ({ ...p, [k]: !p[k] }))

  const equipCount = Object.values(equip).filter(Boolean).length
  const equipTotalValue = useMemo(
    () => ALL_EQUIP_KEYS.reduce((sum, k) => sum + (equip[k] ? (equipValues[k] || 0) : 0), 0),
    [equip, equipValues],
  )
  const roiRanking = useMemo(() => {
    return ALL_EQUIP_KEYS
      .map((k) => {
        const group = EQUIPMENT_GROUPS.find((g) => g.items.some((i) => i.key === k))
        const item = group?.items.find((i) => i.key === k)
        return { key: k, label: item?.label || k, value: equipValues[k] || 0, selected: !!equip[k] }
      })
      .filter((x) => x.value > 0)
      .sort((a, b) => b.value - a.value)
  }, [equipValues, equip])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    setRecs(null)
    try {
      const payload = {
        make: form.make, model: form.model,
        year: parseInt(form.year), body_type: form.body_type,
        mileage: parseFloat(form.mileage), color: form.color,
        fuel_type: form.fuel_type, engine_capacity: parseFloat(form.engine_capacity),
        engine_power: parseFloat(form.engine_power), gearbox: form.gearbox,
        transmission: form.transmission, pollution_standard: form.pollution_standard,
        equipment_count: equipCount,
        ...equip,
      }
      const r = await predictionsApi.predict(payload)
      setResult(r.data)
      loadHistory()
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    } catch (err) {
      setError(err.message || 'Prediction failed. Is the ML model trained?')
    } finally {
      setLoading(false)
    }
  }

  const deleteHistory = async (id) => {
    await predictionsApi.delete(id).catch(() => {})
    loadHistory()
  }

  const fmt = (n) => Number(n).toLocaleString('de-DE')
  const price = result?.predicted_price
  const tier = equipTier(equipCount)

  if (!user) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-[32px] font-bold text-black leading-tight">Price Prediction</h1>
          <p className="text-sm text-as-body mt-1">Enter car specifications to get an AI-powered price estimate</p>
        </div>
        <div className="card flex flex-col items-center justify-center py-20 text-center max-w-sm mx-auto">
          <div className="text-5xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-black mb-2">Sign in to predict prices</h2>
          <p className="text-as-muted text-sm mb-6">
            Create a free account to use the AI price estimator and save your prediction history.
          </p>
          <div className="flex gap-3">
            <Link to="/login" className="btn-primary px-6">Log in</Link>
            <Link to="/register" className="btn-secondary px-6">Create account</Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[32px] font-bold text-black leading-tight">Price Prediction</h1>
        <p className="text-sm text-as-body mt-1">Enter car specifications to get an AI-powered price estimate</p>
      </div>

      {/* ════════ CAR SPECS ════════ */}
      <div className="card">
        <h2 className="font-semibold text-black mb-4">Car Specifications</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-3">
          <div>
            <label className="block text-xs font-medium text-as-body mb-1">Make *</label>
            <select className="select-field text-sm" value={form.make} required
              onChange={(e) => {
                set('make', e.target.value); set('model', '')
                if (e.target.value) makesApi.models(e.target.value).then((r) => setModels(r.data.models || [])).catch(() => setModels([]))
                else setModels([])
              }}>
              <option value="">Select make...</option>
              {(options.makes || []).map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-as-body mb-1">Model *</label>
            {models.length > 0 ? (
              <select className="select-field text-sm" value={form.model} onChange={(e) => set('model', e.target.value)} required>
                <option value="">Select model...</option>
                {models.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : (
              <input type="text" className="input-field text-sm" placeholder="Model name" value={form.model}
                onChange={(e) => set('model', e.target.value)} required />
            )}
          </div>
          <NumberField label="Year *"             name="year"             placeholder="2019"  value={form.year}             onChange={set} />
          <SelectField label="Body Type *"        name="body_type"        opts={modelOptions?.body_types || options.body_types}           value={form.body_type}        onChange={set} required />
          <NumberField label="Engine Capacity *"   name="engine_capacity"  placeholder="1995"  value={form.engine_capacity}  onChange={set} unit="cm³" />
          <NumberField label="Engine Power *"      name="engine_power"     placeholder="150"   value={form.engine_power}     onChange={set} unit="HP" />
          <SelectField label="Fuel Type *"         name="fuel_type"        opts={modelOptions?.fuel_types || options.fuel_types}           value={form.fuel_type}        onChange={set} required />
          <SelectField label="Pollution Std *"     name="pollution_standard" opts={modelOptions?.pollution_standards || options.pollution_standards} value={form.pollution_standard} onChange={set} required />
          <NumberField label="Mileage *"           name="mileage"          placeholder="80000" value={form.mileage}          onChange={set} unit="km" />
          <SelectField label="Color *"             name="color"            opts={modelOptions?.colors || options.colors}                   value={form.color}            onChange={set} required />
          <SelectField label="Gearbox *"           name="gearbox"          opts={modelOptions?.gearboxes || options.gearboxes}             value={form.gearbox}          onChange={set} required />
          <SelectField label="Transmission *"      name="transmission"     opts={modelOptions?.transmissions || options.transmissions}     value={form.transmission}     onChange={set} required />
        </div>
      </div>

      {/* ════════ EQUIPMENT (collapsible) ════════ */}
      <div className="card">
        <button
          type="button"
          className="w-full flex items-center justify-between"
          onClick={() => setShowEquip((p) => !p)}
        >
          <div className="flex items-center gap-3">
            <h2 className="font-semibold text-black">Equipment &amp; Options</h2>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${tier.color}`}>{tier.label}</span>
            {equipCount > 0 && (
              <span className="text-xs text-as-muted">{equipCount} selected</span>
            )}
            {equipTotalValue > 0 && (
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full equip-value-total">
                +€{equipTotalValue.toLocaleString()} value
              </span>
            )}
          </div>
          <span className="text-as-muted text-sm">{showEquip ? '▲' : '▼'}</span>
        </button>

        {showEquip && (
          <div className="mt-4 space-y-4">
            {equipCount > 0 && (
              <div className="flex justify-end">
                <button type="button" onClick={() => setEquip(EMPTY_EQUIP)}
                  className="text-xs text-as-muted hover:text-black underline transition-colors">
                  Clear all
                </button>
              </div>
            )}
            {EQUIPMENT_GROUPS.map((group) => (
              <div key={group.label}>
                <div className="text-[11px] font-semibold text-as-muted uppercase tracking-wider mb-1.5">
                  {group.label}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1.5">
                  {group.items.map(({ key, label }) => {
                    const val = equipValues[key]
                    const on = equip[key]
                    return (
                      <label key={key}
                        className={`flex items-center gap-2 text-xs cursor-pointer rounded-lg px-2.5 py-2 border transition-all select-none
                          ${on
                            ? 'pred-equip-on bg-black/5 border-black text-black font-medium'
                            : 'pred-equip-off bg-white border-[#e8e8e8] text-as-body hover:border-black/40'}`}>
                        <input
                          type="checkbox"
                          className="accent-black w-3.5 h-3.5 flex-shrink-0"
                          checked={on}
                          onChange={() => toggleEquip(key)}
                        />
                        <span className="flex-1 leading-tight">{label}</span>
                        {val > 0 && (
                          <span className={`text-[10px] font-medium flex-shrink-0 ${on ? 'text-emerald-700' : 'text-emerald-600'}`}>
                            +€{val.toLocaleString()}
                          </span>
                        )}
                      </label>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ════════ SUBMIT ════════ */}
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{error}</div>
        )}
        <button type="submit" className="btn-primary w-full py-3 text-base" disabled={loading}>
          {loading ? 'Predicting...' : 'Predict Price'}
        </button>
      </form>

      {/* ════════ RESULT SECTION (full-width, appears after prediction) ════════ */}
      {result && (
        <div ref={resultRef} className="space-y-5">

          {/* Price hero card */}
          <div className="card">
            <div className="flex flex-col md:flex-row md:items-center gap-6">
              {/* Left: big price */}
              <div className="flex-1">
                <div className="text-xs text-as-muted font-semibold uppercase tracking-wider mb-1">
                  Predicted Market Price
                </div>
                <div className="text-5xl font-extrabold text-black">
                  €{fmt(Math.round(price))}
                </div>

                {/* Confidence bar */}
                <div className="mt-3 max-w-md">
                  <div className="flex justify-between text-xs text-as-muted mb-1">
                    <span>€{fmt(Math.round(price - 1986))}</span>
                    <span className="text-black font-semibold">±€{fmt(1986)} MAE</span>
                    <span>€{fmt(Math.round(price + 1986))}</span>
                  </div>
                  <div className="relative h-2 bg-[#f0f0f0] rounded-full overflow-hidden">
                    <div className="absolute inset-y-0 bg-black/15 rounded-full" style={{ left: '10%', right: '10%' }} />
                    <div className="absolute inset-y-0 left-1/2 w-0.5 bg-black -translate-x-1/2" />
                  </div>
                  <p className="text-[11px] text-as-muted mt-1">Likely range based on model accuracy (MAE)</p>
                </div>
              </div>

              {/* Right: car summary */}
              <div className="md:border-l md:border-[#f0f0f0] md:pl-6 text-sm text-as-body space-y-1">
                <div className="font-semibold text-black text-base">{result.input.make} {result.input.model} · {result.input.year}</div>
                <div>{fmt(result.input.mileage)} km · {result.input.engine_power} HP · {result.input.engine_capacity} cm³</div>
                <div>{result.input.fuel_type} · {result.input.gearbox} · {result.input.body_type}</div>
                <div className="flex items-center gap-2 pt-1">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${tier.color}`}>
                    {tier.label} ({equipCount} options)
                  </span>
                  {equipTotalValue > 0 && (
                    <span className="text-xs text-emerald-700 font-medium">+€{equipTotalValue.toLocaleString()} equipment value</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Similar listings + Equipment ROI side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

            {/* Similar Listings — takes 2/3 */}
            <div className="lg:col-span-2 card p-5">
              <h3 className="font-semibold text-black mb-3">Similar Listings on Market</h3>
              {recs === null ? (
                <div className="space-y-2 animate-pulse">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-10 bg-[#f0f0f0] rounded" />
                  ))}
                </div>
              ) : recs.length === 0 ? (
                <p className="text-sm text-as-muted py-6 text-center">No similar listings found for this make/model.</p>
              ) : (
                <div className="overflow-x-auto -mx-5">
                  <table className="min-w-full text-sm">
                    <thead className="bg-[#f9f9f9] border-b border-[#e8e8e8]">
                      <tr>
                        {['Car', 'Year', 'Fuel', 'Mileage', 'Power', 'Gearbox', 'Price', 'Deal Score', ''].map((h) => (
                          <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-as-muted uppercase tracking-wider whitespace-nowrap">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f0f0f0]">
                      {recs.map((car) => (
                        <tr key={car.id} className="hover:bg-as-chip transition-colors">
                          <td className="px-3 py-2.5 whitespace-nowrap">
                            <span className="font-medium text-black">{car.make}</span>{' '}
                            <span className="text-as-body">{car.model}</span>
                          </td>
                          <td className="px-3 py-2.5 text-as-body">{car.year}</td>
                          <td className="px-3 py-2.5 text-as-muted">{car.fuel_type || '—'}</td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">
                            {car.mileage ? `${Number(car.mileage).toLocaleString('de-DE')} km` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">
                            {car.engine_power ? `${car.engine_power} HP` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-as-muted">{car.gearbox || '—'}</td>
                          <td className="px-3 py-2.5 font-semibold text-black whitespace-nowrap">
                            €{Number(car.price).toLocaleString('de-DE')}
                          </td>
                          <td className="px-3 py-2.5 whitespace-nowrap">
                            <DealBadge score={recScores[car.id]} />
                          </td>
                          <td className="px-3 py-2.5">
                            {car.source_url ? (
                              <HoverPeek
                                url={car.source_url}
                                isStatic={true}
                                imageSrc={`${import.meta.env.VITE_API_URL || 'http://localhost:8001/api'}/cars/${car.id}/og-image`}
                                peekWidth={220}
                                peekHeight={138}
                              >
                                <a
                                  href={car.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-blue-500 hover:text-blue-700 underline decoration-dotted whitespace-nowrap"
                                >
                                  View listing
                                </a>
                              </HoverPeek>
                            ) : (
                              <span className="text-as-muted text-xs">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Equipment ROI — takes 1/3 */}
            <div className="card p-5">
              <button
                type="button"
                className="w-full flex items-center justify-between"
                onClick={() => setShowRoi((p) => !p)}
              >
                <h3 className="font-semibold text-black text-sm">Equipment ROI</h3>
                <span className="text-as-muted text-xs">{showRoi ? '▲ Hide' : '▼ Show'}</span>
              </button>
              <p className="text-[11px] text-as-muted mt-1">Which options add the most resale value</p>
              {showRoi && roiRanking.length > 0 && (
                <div className="mt-3 space-y-1 max-h-80 overflow-y-auto">
                  {roiRanking.map((item, i) => (
                    <div
                      key={item.key}
                      className={`flex items-center gap-2 text-xs px-2.5 py-2 rounded-lg transition-colors cursor-pointer ${
                        item.selected
                          ? 'bg-emerald-50 border border-emerald-200 equip-roi-selected'
                          : 'hover:bg-as-chip'
                      }`}
                      onClick={() => toggleEquip(item.key)}
                    >
                      <span className="text-as-muted w-5 text-right flex-shrink-0 tabular-nums">{i + 1}.</span>
                      <span className={`flex-1 ${item.selected ? 'font-medium text-black' : 'text-as-body'}`}>
                        {item.label}
                      </span>
                      <span className={`font-semibold flex-shrink-0 ${item.selected ? 'text-emerald-700' : 'text-emerald-600'}`}>
                        +€{item.value.toLocaleString()}
                      </span>
                      {item.selected && (
                        <span className="text-emerald-500 text-[10px]">✓</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Placeholder when no result yet */}
      {!result && !loading && (
        <div className="card border-2 border-dashed border-[#e0e0e0] flex flex-col items-center justify-center py-14 text-center">
          <div className="text-4xl mb-3">🤖</div>
          <div className="text-as-muted text-sm">Fill in the car specs above, select equipment, and click Predict Price</div>
        </div>
      )}

      {/* ════════ PREDICTION HISTORY ════════ */}
      {history.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-black mb-4">Recent Predictions</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-[#f9f9f9]">
                <tr>
                  {['Car', 'Year', 'Mileage', 'Fuel', 'Gearbox', 'Predicted Price', 'Date', ''].map((h) => (
                    <th key={h} className="px-3 py-2 text-left text-xs font-semibold text-as-muted uppercase whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0f0f0]">
                {history.map((p) => (
                  <tr key={p.id} className="hover:bg-as-chip">
                    <td className="px-3 py-2">
                      <span className="font-medium">{p.make}</span>{' '}
                      <span className="text-as-body">{p.model}</span>
                    </td>
                    <td className="px-3 py-2 text-as-body">{p.year}</td>
                    <td className="px-3 py-2 text-as-muted">{p.mileage ? `${fmt(p.mileage)} km` : '—'}</td>
                    <td className="px-3 py-2 text-as-muted">{p.fuel_type}</td>
                    <td className="px-3 py-2 text-as-muted">{p.gearbox}</td>
                    <td className="px-3 py-2 font-semibold text-black">€{fmt(Math.round(p.predicted_price))}</td>
                    <td className="px-3 py-2 text-as-muted text-xs whitespace-nowrap">
                      {p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-3 py-2">
                      <button className="text-as-muted hover:text-black text-lg leading-none transition-colors"
                        onClick={() => deleteHistory(p.id)}>×</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
