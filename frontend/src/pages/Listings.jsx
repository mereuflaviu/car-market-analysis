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

export default function Listings() {
  const [cars, setCars] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [options, setOptions] = useState({})

  const [filters, setFilters] = useState({
    make: '', fuel_type: '', body_type: '', gearbox: '',
    year_min: '', year_max: '', price_min: '', price_max: '',
  })

  const [showForm, setShowForm] = useState(false)
  const [editCar, setEditCar] = useState(null)

  const PAGE_SIZE = 20

  useEffect(() => {
    makesApi.options().then((r) => setOptions(r.data)).catch(console.error)
  }, [])

  const fetchCars = useCallback(
    async (p) => {
      setLoading(true)
      try {
        const params = {
          page: p,
          page_size: PAGE_SIZE,
          ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '')),
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
    setFilters((p) => ({ ...p, [key]: value }))
    setPage(1)
  }

  const clearFilters = () => {
    setFilters({ make: '', fuel_type: '', body_type: '', gearbox: '', year_min: '', year_max: '', price_min: '', price_max: '' })
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
        <aside className="w-48 flex-shrink-0">
          <div className="card p-4 space-y-3">
            <div className="font-semibold text-slate-700 text-sm">Filters</div>

            {[
              { label: 'Make', key: 'make', opts: options.makes, placeholder: 'All makes' },
              { label: 'Fuel Type', key: 'fuel_type', opts: options.fuel_types, placeholder: 'All fuels' },
              { label: 'Body Type', key: 'body_type', opts: options.body_types, placeholder: 'All types' },
              { label: 'Gearbox', key: 'gearbox', opts: options.gearboxes, placeholder: 'All' },
            ].map(({ label, key, opts, placeholder }) => (
              <div key={key}>
                <label className="text-xs text-slate-500 mb-1 block">{label}</label>
                <select
                  className="select-field text-xs py-1.5"
                  value={filters[key]}
                  onChange={(e) => handleFilter(key, e.target.value)}
                >
                  <option value="">{placeholder}</option>
                  {(opts || []).map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </div>
            ))}

            {[
              { label: 'Year min', key: 'year_min', placeholder: '2010' },
              { label: 'Year max', key: 'year_max', placeholder: '2024' },
              { label: 'Min price (€)', key: 'price_min', placeholder: '0' },
              { label: 'Max price (€)', key: 'price_max', placeholder: '100000' },
            ].map(({ label, key, placeholder }) => (
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
            ))}

            <button className="w-full btn-secondary text-xs py-1.5" onClick={clearFilters}>
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
                      {['Make', 'Model', 'Year', 'Body', 'Fuel', 'Mileage', 'Power', 'Gearbox', 'Price', ''].map(
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
                        <td colSpan={10} className="px-4 py-10 text-center text-slate-400">
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
