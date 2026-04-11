import { useState, useEffect, useCallback } from 'react'
import { carsApi, makesApi } from '../api/client'
import CarForm from '../components/CarForm'

function Pagination({ page, total, pageSize, onChange }) {
  const totalPages = Math.ceil(total / pageSize)
  if (totalPages <= 1) return null
  return (
    <div className="flex items-center gap-3 justify-center mt-4 text-sm">
      <button
        className="btn-secondary py-1 px-3 disabled:opacity-40"
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
      >
        ← Prev
      </button>
      <span className="text-slate-500">
        Page {page} / {totalPages} &nbsp;·&nbsp; {total.toLocaleString()} results
      </span>
      <button
        className="btn-secondary py-1 px-3 disabled:opacity-40"
        disabled={page === totalPages}
        onClick={() => onChange(page + 1)}
      >
        Next →
      </button>
    </div>
  )
}

const EMPTY_FILTERS = {
  make: '', model: '', fuel_type: '', body_type: '', gearbox: '', transmission: '',
  year_min: '', year_max: '', price_min: '', price_max: '',
  mileage_min: '', mileage_max: '', power_min: '', power_max: '',
  sort_by: 'price', sort_dir: 'asc',
}

export default function Listings() {
  const [cars, setCars] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [options, setOptions] = useState({})
  const [models, setModels] = useState([])

  const [filters, setFilters] = useState(EMPTY_FILTERS)

  const [showForm, setShowForm] = useState(false)
  const [editCar, setEditCar] = useState(null)

  const PAGE_SIZE = 20

  useEffect(() => {
    makesApi.options().then((r) => setOptions(r.data)).catch(console.error)
  }, [])

  // Load models when make changes
  useEffect(() => {
    if (filters.make) {
      makesApi.models(filters.make)
        .then((r) => setModels(r.data.models || []))
        .catch(() => setModels([]))
    } else {
      setModels([])
    }
  }, [filters.make])

  const fetchCars = useCallback(
    async (p) => {
      setLoading(true)
      try {
        const params = { page: p, page_size: PAGE_SIZE }
        const skip = ['mileage_min', 'mileage_max', 'power_min', 'power_max']
        for (const [k, v] of Object.entries(filters)) {
          if (v === '') continue
          // Backend uses year_min/max, price_min/max, sort_by, sort_dir directly
          // mileage and power range not yet in backend — we filter client-side below
          if (!skip.includes(k)) params[k] = v
        }
        const res = await carsApi.list(params)
        let items = res.data.items
        // Client-side mileage / power filtering (backend doesn't expose these yet)
        if (filters.mileage_min !== '') items = items.filter(c => c.mileage == null || c.mileage >= Number(filters.mileage_min))
        if (filters.mileage_max !== '') items = items.filter(c => c.mileage == null || c.mileage <= Number(filters.mileage_max))
        if (filters.power_min !== '') items = items.filter(c => c.engine_power == null || c.engine_power >= Number(filters.power_min))
        if (filters.power_max !== '') items = items.filter(c => c.engine_power == null || c.engine_power <= Number(filters.power_max))
        setCars(items)
        setTotal(res.data.total)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    },
    [filters],
  )

  useEffect(() => {
    fetchCars(page)
  }, [page, fetchCars])

  const handleFilter = (key, value) => {
    setFilters((p) => {
      const next = { ...p, [key]: value }
      // Reset model when make changes
      if (key === 'make') next.model = ''
      return next
    })
    setPage(1)
  }

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS)
    setModels([])
    setPage(1)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this listing?')) return
    try {
      await carsApi.delete(id)
      fetchCars(page)
    } catch {
      alert('Failed to delete.')
    }
  }

  const handleFormClose = (refresh) => {
    setShowForm(false)
    setEditCar(null)
    if (refresh) fetchCars(page)
  }

  const fmt = (n) => (n != null ? Number(n).toLocaleString() : '—')

  const selField = (label, key, opts, placeholder) => (
    <div key={key}>
      <label className="text-xs text-slate-500 mb-1 block">{label}</label>
      <select
        className="select-field text-xs py-1.5"
        value={filters[key]}
        onChange={(e) => handleFilter(key, e.target.value)}
      >
        <option value="">{placeholder}</option>
        {(opts || []).map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )

  const numField = (label, key, placeholder) => (
    <div key={key}>
      <label className="text-xs text-slate-500 mb-1 block">{label}</label>
      <input
        type="number"
        className="input-field text-xs py-1.5"
        placeholder={placeholder}
        value={filters[key]}
        onChange={(e) => handleFilter(key, e.target.value)}
      />
    </div>
  )

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Car Listings</h1>
          <p className="text-sm text-slate-500 mt-0.5">{total.toLocaleString()} results</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => { setEditCar(null); setShowForm(true) }}
        >
          + Add Car
        </button>
      </div>

      <div className="flex gap-5">
        {/* Filter sidebar */}
        <aside className="w-56 flex-shrink-0">
          <div className="card p-4 space-y-3">
            <div className="font-semibold text-slate-700 text-sm">Filters</div>

            {/* Make & Model (cascading) */}
            {selField('Make', 'make', options.makes, 'All makes')}
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Model</label>
              {models.length > 0 ? (
                <select
                  className="select-field text-xs py-1.5"
                  value={filters.model}
                  onChange={(e) => handleFilter('model', e.target.value)}
                >
                  <option value="">All models</option>
                  {models.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              ) : (
                <input
                  type="text"
                  className="input-field text-xs py-1.5"
                  placeholder={filters.make ? 'Type model…' : 'Select make first'}
                  value={filters.model}
                  onChange={(e) => handleFilter('model', e.target.value)}
                  disabled={!filters.make}
                />
              )}
            </div>

            <div className="border-t border-slate-100 pt-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Type
            </div>
            {selField('Fuel Type', 'fuel_type', options.fuel_types, 'All fuels')}
            {selField('Body Type', 'body_type', options.body_types, 'All types')}
            {selField('Gearbox', 'gearbox', options.gearboxes, 'All')}
            {selField('Transmission', 'transmission', options.transmissions, 'All')}

            <div className="border-t border-slate-100 pt-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Year
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('From', 'year_min', '2010')}
              {numField('To', 'year_max', '2024')}
            </div>

            <div className="border-t border-slate-100 pt-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Price (€)
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('Min', 'price_min', '0')}
              {numField('Max', 'price_max', '100k')}
            </div>

            <div className="border-t border-slate-100 pt-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Mileage (km)
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('Min', 'mileage_min', '0')}
              {numField('Max', 'mileage_max', '300k')}
            </div>

            <div className="border-t border-slate-100 pt-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Power (HP)
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('Min', 'power_min', '70')}
              {numField('Max', 'power_max', '500')}
            </div>

            <div className="border-t border-slate-100 pt-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Sort
            </div>
            {selField('Sort by', 'sort_by', ['price', 'year', 'mileage', 'engine_power', 'make'], 'Default')}
            {selField('Direction', 'sort_dir', ['asc', 'desc'], 'Asc')}

            <button className="w-full btn-secondary text-xs py-1.5 mt-1" onClick={clearFilters}>
              Clear filters
            </button>
          </div>
        </aside>

        {/* Table */}
        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="card flex items-center justify-center h-40 text-slate-400 animate-pulse">
              Loading…
            </div>
          ) : (
            <>
              <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      {['Make', 'Model', 'Year', 'Body', 'Fuel', 'Mileage', 'Power', 'Gearbox', 'Trans.', 'Price', ''].map(
                        (h) => (
                          <th
                            key={h}
                            className="px-3 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap"
                          >
                            {h}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {cars.length === 0 ? (
                      <tr>
                        <td colSpan={11} className="px-4 py-10 text-center text-slate-400">
                          No cars found matching your filters.
                        </td>
                      </tr>
                    ) : (
                      cars.map((car) => (
                        <tr key={car.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-3 py-2.5 font-medium whitespace-nowrap">{car.make}</td>
                          <td className="px-3 py-2.5 text-slate-600 whitespace-nowrap">{car.model}</td>
                          <td className="px-3 py-2.5 text-slate-600">{car.year}</td>
                          <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">{car.body_type || '—'}</td>
                          <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">{car.fuel_type || '—'}</td>
                          <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">
                            {car.mileage ? `${fmt(car.mileage)} km` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">
                            {car.engine_power ? `${car.engine_power} HP` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">{car.gearbox || '—'}</td>
                          <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">{car.transmission || '—'}</td>
                          <td className="px-3 py-2.5 font-semibold text-blue-700 whitespace-nowrap">
                            €{fmt(car.price)}
                          </td>
                          <td className="px-3 py-2.5">
                            <div className="flex gap-1">
                              <button
                                className="text-xs text-slate-500 hover:text-blue-600 px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                                onClick={() => { setEditCar(car); setShowForm(true) }}
                              >
                                Edit
                              </button>
                              <button
                                className="text-xs text-red-400 hover:text-red-600 px-2 py-1 rounded hover:bg-red-50 transition-colors"
                                onClick={() => handleDelete(car.id)}
                              >
                                Del
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              <Pagination page={page} total={total} pageSize={PAGE_SIZE} onChange={setPage} />
            </>
          )}
        </div>
      </div>

      {showForm && (
        <CarForm car={editCar} options={options} onClose={handleFormClose} />
      )}
    </div>
  )
}
