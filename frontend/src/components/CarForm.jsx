import { useState, useEffect } from 'react'
import { carsApi, makesApi } from '../api/client'

const EMPTY = {
  make: '', model: '', year: '', body_type: '', mileage: '',
  door_count: '', nr_seats: '', color: '', fuel_type: '',
  engine_capacity: '', engine_power: '', gearbox: '',
  transmission: '', pollution_standard: '', price: '',
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

  const SelectField = ({ label, name, opts, required }) => (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">{label}</label>
      <select
        className="select-field"
        value={form[name]}
        onChange={(e) => set(name, e.target.value)}
        required={required}
      >
        <option value="">Select…</option>
        {(opts || []).map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  )

  const NumberField = ({ label, name, placeholder, required }) => (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">{label}</label>
      <input
        type="number"
        className="input-field"
        placeholder={placeholder}
        value={form[name]}
        onChange={(e) => set(name, e.target.value)}
        required={required}
      />
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[92vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold text-slate-800">
            {car ? 'Edit Car Listing' : 'Add New Car Listing'}
          </h2>
          <button
            onClick={() => onClose(false)}
            className="text-slate-400 hover:text-slate-600 text-2xl font-light leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 grid grid-cols-2 gap-4">
          {/* Make */}
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Make *</label>
            <select
              className="select-field"
              value={form.make}
              onChange={(e) => {
                set('make', e.target.value)
                set('model', '')
              }}
              required
            >
              <option value="">Select make…</option>
              {(options.makes || []).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Model */}
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Model *</label>
            {models.length > 0 ? (
              <select
                className="select-field"
                value={form.model}
                onChange={(e) => set('model', e.target.value)}
                required
              >
                <option value="">Select model…</option>
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
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

          <NumberField label="Year *" name="year" placeholder="2019" required />
          <NumberField label="Price (€) *" name="price" placeholder="15000" required />
          <SelectField label="Body Type" name="body_type" opts={options.body_types} />
          <SelectField label="Fuel Type" name="fuel_type" opts={options.fuel_types} />
          <NumberField label="Mileage (km)" name="mileage" placeholder="80000" />
          <NumberField label="Engine Power (HP)" name="engine_power" placeholder="150" />
          <NumberField label="Engine Capacity (cm³)" name="engine_capacity" placeholder="1995" />
          <SelectField label="Gearbox" name="gearbox" opts={options.gearboxes} />
          <SelectField label="Transmission" name="transmission" opts={options.transmissions} />
          <SelectField label="Pollution Standard" name="pollution_standard" opts={options.pollution_standards} />
          <SelectField label="Color" name="color" opts={options.colors} />
          <NumberField label="Door Count" name="door_count" placeholder="5" />
          <NumberField label="Nr. Seats" name="nr_seats" placeholder="5" />

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
