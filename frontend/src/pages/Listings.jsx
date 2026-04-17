import { useState, useEffect, useCallback } from 'react'
import { carsApi, makesApi } from '../api/client'
import CarForm from '../components/CarForm'
import { useAuth } from '../context/AuthContext'
import { HoverPeek } from '../components/ui/link-preview'

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
      <span className="text-as-muted">
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
  mine: false,
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

  const { user } = useAuth()
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
        for (const [k, v] of Object.entries(filters)) {
          if (v === '' || v === false) continue
          params[k] = v
        }
        const res = await carsApi.list(params)
        setCars(res.data.items)
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
      <label className="text-xs text-as-muted mb-1 block">{label}</label>
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
      <label className="text-xs text-as-muted mb-1 block">{label}</label>
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
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[32px] font-bold text-black leading-tight">Car Listings</h1>
          <p className="text-sm text-as-body mt-0.5">{total.toLocaleString()} results</p>
        </div>
        <div className="flex items-center gap-2">
          {user && (
            <button
              type="button"
              onClick={() => { setFilters(f => ({ ...f, mine: !f.mine })); setPage(1) }}
              className={`px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
                filters.mine
                  ? 'bg-black text-white'
                  : 'bg-as-chip text-black hover:bg-as-hover'
              }`}
            >
              My Listings
            </button>
          )}
          {user && (
            <button
              className="btn-primary"
              onClick={() => { setEditCar(null); setShowForm(true) }}
            >
              + Add Car
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-5">
        {/* Filter sidebar */}
        <aside className="w-56 flex-shrink-0">
          <div className="card p-4 space-y-3">
            <div className="font-semibold text-black text-sm">Filters</div>

            {/* Make & Model (cascading) */}
            {selField('Make', 'make', options.makes, 'All makes')}
            <div>
              <label className="text-xs text-as-muted mb-1 block">Model</label>
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

            <div className="border-t border-[#f0f0f0] pt-2 text-xs font-semibold text-as-muted uppercase tracking-wider">
              Type
            </div>
            {selField('Fuel Type', 'fuel_type', options.fuel_types, 'All fuels')}
            {selField('Body Type', 'body_type', options.body_types, 'All types')}
            {selField('Gearbox', 'gearbox', options.gearboxes, 'All')}
            {selField('Transmission', 'transmission', options.transmissions, 'All')}

            <div className="border-t border-[#f0f0f0] pt-2 text-xs font-semibold text-as-muted uppercase tracking-wider">
              Year
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('From', 'year_min', '2010')}
              {numField('To', 'year_max', '2024')}
            </div>

            <div className="border-t border-[#f0f0f0] pt-2 text-xs font-semibold text-as-muted uppercase tracking-wider">
              Price (€)
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('Min', 'price_min', '0')}
              {numField('Max', 'price_max', '100k')}
            </div>

            <div className="border-t border-[#f0f0f0] pt-2 text-xs font-semibold text-as-muted uppercase tracking-wider">
              Mileage (km)
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('Min', 'mileage_min', '0')}
              {numField('Max', 'mileage_max', '300k')}
            </div>

            <div className="border-t border-[#f0f0f0] pt-2 text-xs font-semibold text-as-muted uppercase tracking-wider">
              Power (HP)
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {numField('Min', 'power_min', '70')}
              {numField('Max', 'power_max', '500')}
            </div>

            <div className="border-t border-[#f0f0f0] pt-2 text-xs font-semibold text-as-muted uppercase tracking-wider">
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
            <div className="card flex items-center justify-center h-40 text-as-muted animate-pulse">
              Loading…
            </div>
          ) : (
            <>
              <div className="overflow-x-auto rounded-xl border border-[#e8e8e8] bg-white">
                <table className="min-w-full text-sm">
                  <thead className="bg-[#f9f9f9] border-b border-[#e8e8e8]">
                    <tr>
                      {['Make', 'Model', 'Year', 'Body', 'Fuel', 'Mileage', 'Power', 'Gearbox', 'Trans.', 'Price', 'Source', ''].map(
                        (h) => (
                          <th
                            key={h}
                            className="px-3 py-3 text-left text-xs font-semibold text-as-muted uppercase tracking-wider whitespace-nowrap"
                          >
                            {h}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f0f0f0]">
                    {cars.length === 0 ? (
                      <tr>
                        <td colSpan={11} className="px-4 py-10 text-center text-as-muted">
                          No cars found matching your filters.
                        </td>
                      </tr>
                    ) : (
                      cars.map((car) => (
                        <tr key={car.id} className="hover:bg-as-chip transition-colors">
                          <td className="px-3 py-2.5 font-medium whitespace-nowrap">{car.make}</td>
                          <td className="px-3 py-2.5 text-as-body whitespace-nowrap">{car.model}</td>
                          <td className="px-3 py-2.5 text-as-body">{car.year}</td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">{car.body_type || '—'}</td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">{car.fuel_type || '—'}</td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">
                            {car.mileage ? `${fmt(car.mileage)} km` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">
                            {car.engine_power ? `${car.engine_power} HP` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">{car.gearbox || '—'}</td>
                          <td className="px-3 py-2.5 text-as-muted whitespace-nowrap">{car.transmission || '—'}</td>
                          <td className="px-3 py-2.5 font-semibold text-black whitespace-nowrap">
                            €{fmt(car.price)}
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
                                  Autovit →
                                </a>
                              </HoverPeek>
                            ) : (
                              <span className="text-xs text-as-muted">—</span>
                            )}
                          </td>
                          <td className="px-3 py-2.5">
                            {(user?.role === 'admin' || user?.id === car.user_id) && (
                              <div className="flex gap-1">
                                <button
                                  className="text-xs text-as-muted hover:text-black px-2 py-1 rounded hover:bg-as-chip transition-colors"
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
                            )}
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
