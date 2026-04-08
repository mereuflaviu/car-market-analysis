import { useState, useEffect } from 'react'
import { predictionsApi, makesApi } from '../api/client'

const DEFAULTS = {
  make: '', model: '', year: '2019', body_type: 'SUV',
  mileage: '80000', color: 'Negru', fuel_type: 'Diesel',
  engine_capacity: '1995', engine_power: '150',
  gearbox: 'Manuala', transmission: 'Fata', pollution_standard: 'Euro 6',
}

function SelectField({ label, name, opts, value, onChange, required }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">{label}</label>
      <select
        className="select-field"
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        required={required}
      >
        <option value="">Select…</option>
        {(opts || []).map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )
}

function NumberField({ label, name, placeholder, value, onChange }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">{label}</label>
      <input
        type="number"
        className="input-field"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(name, e.target.value)}
        required
      />
    </div>
  )
}

export default function Prediction() {
  const [form, setForm] = useState(DEFAULTS)
  const [options, setOptions] = useState({})
  const [models, setModels] = useState([])
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [modelInfo, setModelInfo] = useState(null)

  useEffect(() => {
    makesApi.options().then((r) => setOptions(r.data)).catch(() => {})
    predictionsApi.modelInfo().then((r) => setModelInfo(r.data)).catch(() => {})
    loadHistory()
  }, [])

  useEffect(() => {
    if (form.make) {
      makesApi.models(form.make)
        .then((r) => setModels(r.data.models || []))
        .catch(() => setModels([]))
    } else {
      setModels([])
    }
  }, [form.make])

  const loadHistory = () => {
    predictionsApi.history({ limit: 10 }).then((r) => setHistory(r.data)).catch(() => {})
  }

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const payload = {
        make: form.make,
        model: form.model,
        year: parseInt(form.year),
        body_type: form.body_type,
        mileage: parseFloat(form.mileage),
        color: form.color,
        fuel_type: form.fuel_type,
        engine_capacity: parseFloat(form.engine_capacity),
        engine_power: parseFloat(form.engine_power),
        gearbox: form.gearbox,
        transmission: form.transmission,
        pollution_standard: form.pollution_standard,
      }
      const r = await predictionsApi.predict(payload)
      setResult(r.data)
      loadHistory()
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Is the ML model trained?')
    } finally {
      setLoading(false)
    }
  }

  const deleteHistory = async (id) => {
    await predictionsApi.delete(id).catch(() => {})
    loadHistory()
  }

  const fmt = (n) => Number(n).toLocaleString('de-DE')

  // SelectField and NumberField are defined outside this component to avoid focus loss

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Price Prediction</h1>
        <p className="text-sm text-slate-500 mt-1">
          Enter car specifications to get an AI-powered price estimate
        </p>
      </div>

      {/* Model status banner */}
      {modelInfo && (
        <div
          className={`card py-3 border-l-4 ${
            modelInfo.status === 'ready' ? 'border-l-green-500 bg-green-50' : 'border-l-yellow-500 bg-yellow-50'
          }`}
        >
          {modelInfo.status === 'ready' ? (
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <span className="text-green-700 font-semibold">✓ XGBoost model ready</span>
              <span className="text-slate-500">
                R² = {modelInfo.r2?.toFixed(4)} &nbsp;·&nbsp; MAE = €{Math.round(modelInfo.mae || 0).toLocaleString()}
              </span>
            </div>
          ) : (
            <div className="text-yellow-800 text-sm">
              ⚠ Model not trained. Run:{' '}
              <code className="bg-yellow-100 px-1.5 py-0.5 rounded font-mono text-xs">
                cd backend &amp;&amp; python app/ml/train.py
              </code>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <div className="lg:col-span-2 card">
          <h2 className="font-semibold text-slate-700 mb-5">Car Specifications</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            {/* Make */}
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Make *</label>
              <select
                className="select-field"
                value={form.make}
                onChange={(e) => {
                  set('make', e.target.value)
                  set('model', '')
                  if (e.target.value) {
                    makesApi.models(e.target.value)
                      .then((r) => setModels(r.data.models || []))
                      .catch(() => setModels([]))
                  } else {
                    setModels([])
                  }
                }}
                required
              >
                <option value="">Select make…</option>
                {(options.makes || []).map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>

            {/* Model */}
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Model *</label>
              {models.length > 0 ? (
                <select className="select-field" value={form.model} onChange={(e) => set('model', e.target.value)} required>
                  <option value="">Select model…</option>
                  {models.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              ) : (
                <input type="text" className="input-field" placeholder="Model name" value={form.model} onChange={(e) => set('model', e.target.value)} required />
              )}
            </div>

            <NumberField label="Year *" name="year" placeholder="2019" value={form.year} onChange={set} />
            <NumberField label="Mileage (km) *" name="mileage" placeholder="80000" value={form.mileage} onChange={set} />
            <NumberField label="Engine Capacity (cm³) *" name="engine_capacity" placeholder="1995" value={form.engine_capacity} onChange={set} />
            <NumberField label="Engine Power (HP) *" name="engine_power" placeholder="150" value={form.engine_power} onChange={set} />
            <SelectField label="Body Type *" name="body_type" opts={options.body_types} value={form.body_type} onChange={set} required />
            <SelectField label="Fuel Type *" name="fuel_type" opts={options.fuel_types} value={form.fuel_type} onChange={set} required />
            <SelectField label="Gearbox *" name="gearbox" opts={options.gearboxes} value={form.gearbox} onChange={set} required />
            <SelectField label="Transmission *" name="transmission" opts={options.transmissions} value={form.transmission} onChange={set} required />
            <SelectField label="Pollution Standard *" name="pollution_standard" opts={options.pollution_standards} value={form.pollution_standard} onChange={set} required />
            <SelectField label="Color *" name="color" opts={options.colors} value={form.color} onChange={set} required />

            {error && (
              <div className="col-span-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
                {error}
              </div>
            )}

            <div className="col-span-2">
              <button type="submit" className="btn-primary w-full py-3 text-base" disabled={loading}>
                {loading ? '⏳ Predicting…' : '🤖 Predict Price'}
              </button>
            </div>
          </form>
        </div>

        {/* Result + model info */}
        <div className="space-y-4">
          {result ? (
            <div className="card border-2 border-blue-300 bg-gradient-to-br from-blue-50 to-white">
              <div className="text-xs text-blue-600 font-semibold uppercase tracking-wider mb-2">
                Predicted Market Price
              </div>
              <div className="text-5xl font-extrabold text-blue-800 mb-3">
                €{fmt(Math.round(result.predicted_price))}
              </div>
              <div className="text-xs text-slate-500 space-y-1 border-t border-blue-100 pt-3">
                <div>
                  <strong>{result.input.make} {result.input.model}</strong> · {result.input.year}
                </div>
                <div>{fmt(result.input.mileage)} km · {result.input.engine_power} HP</div>
                <div>{result.input.fuel_type} · {result.input.gearbox} · {result.input.body_type}</div>
              </div>
              <div className="mt-3 pt-3 border-t border-blue-100 text-xs text-blue-400">
                MAE ≈ €3,037 — actual market price likely within this range
              </div>
            </div>
          ) : (
            <div className="card border-2 border-dashed border-slate-200 flex flex-col items-center justify-center py-14 text-center">
              <div className="text-4xl mb-3">🤖</div>
              <div className="text-slate-400 text-sm">Fill in the form and click<br />Predict Price</div>
            </div>
          )}

          <div className="card p-4">
            <div className="text-xs font-semibold text-slate-600 mb-3">Model Details</div>
            <dl className="space-y-2 text-xs">
              {[
                ['Algorithm', 'XGBoost Regressor'],
                ['R² Score', '0.8951'],
                ['MAE', '€3,037'],
                ['RMSE', '€5,194'],
                ['Training samples', '1,514'],
                ['Test samples', '379'],
                ['Features', '12'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-slate-500">{k}</span>
                  <span className="font-medium text-slate-700">{v}</span>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* Prediction history */}
      {history.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">Recent Predictions</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {['Make', 'Model', 'Year', 'Mileage', 'Fuel', 'Gearbox', 'Predicted Price', 'Date', ''].map(
                    (h) => (
                      <th key={h} className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase whitespace-nowrap">
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium">{p.make}</td>
                    <td className="px-3 py-2 text-slate-600">{p.model}</td>
                    <td className="px-3 py-2 text-slate-600">{p.year}</td>
                    <td className="px-3 py-2 text-slate-500">{p.mileage ? `${fmt(p.mileage)} km` : '—'}</td>
                    <td className="px-3 py-2 text-slate-500">{p.fuel_type}</td>
                    <td className="px-3 py-2 text-slate-500">{p.gearbox}</td>
                    <td className="px-3 py-2 font-bold text-blue-700">€{fmt(Math.round(p.predicted_price))}</td>
                    <td className="px-3 py-2 text-slate-400 text-xs whitespace-nowrap">
                      {p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-3 py-2">
                      <button
                        className="text-slate-300 hover:text-red-400 text-lg leading-none"
                        onClick={() => deleteHistory(p.id)}
                      >
                        ×
                      </button>
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
