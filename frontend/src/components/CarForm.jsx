import { useState, useEffect } from 'react'
import { carsApi, makesApi } from '../api/client'

const EMPTY = {
  make: '', model: '', year: '', body_type: '', mileage: '',
  door_count: '', nr_seats: '', color: '', fuel_type: '',
  engine_capacity: '', engine_power: '', gearbox: '',
  transmission: '', pollution_standard: '', price: '',
}

// Defined outside CarForm to prevent remount on every render (fixes focus loss bug)
function SelectField({ label, name, opts, value, onChange, required }) {
  return (
    <div>
      <label className="block text-xs font-medium text-as-body mb-1">{label}</label>
      <select
        className="select-field"
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        required={required}
      >
        <option value="">Select…</option>
        {(opts || []).map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  )
}

function NumberField({ label, name, placeholder, value, onChange, required }) {
  return (
    <div>
      <label className="block text-xs font-medium text-as-body mb-1">{label}</label>
      <input
        type="number"
        className="input-field"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        required={required}
      />
    </div>
  )
}

export default function CarForm({ car, options, onClose }) {
  const [form, setForm] = useState(
    car
      ? {
          ...car,
          year: String(car.year ?? ''),
          mileage: String(car.mileage ?? ''),
          door_count: String(car.door_count ?? ''),
          nr_seats: String(car.nr_seats ?? ''),
          engine_capacity: String(car.engine_capacity ?? ''),
          engine_power: String(car.engine_power ?? ''),
          price: String(car.price ?? ''),
        }
      : EMPTY,
  )
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (form.make) {
      makesApi
        .models(form.make)
        .then((r) => setModels(r.data.models || []))
        .catch(() => setModels([]))
    }
  }, [form.make])

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = {
        make: form.make,
        model: form.model,
        year: parseInt(form.year),
        body_type: form.body_type || null,
        mileage: form.mileage ? parseFloat(form.mileage) : null,
        door_count: form.door_count ? parseInt(form.door_count) : null,
        nr_seats: form.nr_seats ? parseInt(form.nr_seats) : null,
        color: form.color || null,
        fuel_type: form.fuel_type || null,
        engine_capacity: form.engine_capacity ? parseFloat(form.engine_capacity) : null,
        engine_power: form.engine_power ? parseFloat(form.engine_power) : null,
        gearbox: form.gearbox || null,
        transmission: form.transmission || null,
        pollution_standard: form.pollution_standard || null,
        price: parseFloat(form.price),
      }
      if (car?.id) {
        await carsApi.update(car.id, payload)
      } else {
        await carsApi.create(payload)
      }
      onClose(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[92vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-black sticky top-0 bg-white z-10">
          <h2 className="text-lg font-bold text-black">
            {car ? 'Edit Car Listing' : 'Add New Car Listing'}
          </h2>
          <button
            onClick={() => onClose(false)}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-as-chip hover:bg-as-hover text-black transition-colors"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 grid grid-cols-2 gap-4">
          {/* Make */}
          <div>
            <label className="block text-xs font-medium text-as-body mb-1">Make *</label>
            <select
              className="select-field"
              value={form.make}
              onChange={(e) => { set('make', e.target.value); set('model', '') }}
              required
            >
              <option value="">Select make…</option>
              {(options.makes || []).map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Model */}
          <div>
            <label className="block text-xs font-medium text-as-body mb-1">Model *</label>
            {models.length > 0 ? (
              <select
                className="select-field"
                value={form.model}
                onChange={(e) => set('model', e.target.value)}
                required
              >
                <option value="">Select model…</option>
                {models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                className="input-field"
                placeholder="Type model name"
                value={form.model}
                onChange={(e) => set('model', e.target.value)}
                required
              />
            )}
          </div>

          <NumberField label="Year *"              name="year"              placeholder="2019"  value={form.year}              onChange={set} required />
          <NumberField label="Price (€) *"         name="price"             placeholder="15000" value={form.price}             onChange={set} required />
          <SelectField label="Body Type"           name="body_type"         opts={options.body_types}          value={form.body_type}          onChange={set} />
          <SelectField label="Fuel Type"           name="fuel_type"         opts={options.fuel_types}          value={form.fuel_type}          onChange={set} />
          <NumberField label="Mileage (km)"        name="mileage"           placeholder="80000" value={form.mileage}           onChange={set} />
          <NumberField label="Engine Power (HP)"   name="engine_power"      placeholder="150"   value={form.engine_power}      onChange={set} />
          <NumberField label="Engine Capacity (cm³)" name="engine_capacity" placeholder="1995"  value={form.engine_capacity}   onChange={set} />
          <SelectField label="Gearbox"             name="gearbox"           opts={options.gearboxes}           value={form.gearbox}           onChange={set} />
          <SelectField label="Transmission"        name="transmission"      opts={options.transmissions}       value={form.transmission}      onChange={set} />
          <SelectField label="Pollution Standard"  name="pollution_standard" opts={options.pollution_standards} value={form.pollution_standard} onChange={set} />
          <SelectField label="Color"               name="color"             opts={options.colors}              value={form.color}             onChange={set} />
          <NumberField label="Door Count"          name="door_count"        placeholder="5"     value={form.door_count}        onChange={set} />
          <NumberField label="Nr. Seats"           name="nr_seats"          placeholder="5"     value={form.nr_seats}          onChange={set} />

          {error && (
            <div className="col-span-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <div className="col-span-2 flex gap-3 pt-2">
            <button type="submit" className="btn-primary flex-1" disabled={loading}>
              {loading ? 'Saving…' : car ? 'Update Car' : 'Add Car'}
            </button>
            <button type="button" className="btn-secondary" onClick={() => onClose(false)}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
