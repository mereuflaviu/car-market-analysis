import { useState, useEffect, useCallback, useRef } from 'react'
import { adminApi } from '../api/client'

function StatusBadge({ status }) {
  const styles = {
    success: 'bg-green-50 text-green-700',
    running: 'bg-blue-50 text-blue-700 animate-pulse',
    failed:  'bg-red-50 text-red-600',
    partial: 'bg-yellow-50 text-yellow-700',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${styles[status] ?? 'bg-as-chip text-as-body'}`}>
      {status}
    </span>
  )
}

function duration(start, end) {
  if (!start) return '—'
  const ms = new Date(end ?? Date.now()) - new Date(start)
  const mins = Math.floor(ms / 60000)
  const secs = Math.floor((ms % 60000) / 1000)
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

export default function AdminPipeline() {
  const [status, setStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [triggering, setTriggering] = useState(null) // 'daily' | 'full_sweep' | 'retrain'
  const [toast, setToast] = useState(null)
  const pollRef = useRef(null)

  const showToast = (msg, type = 'ok') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  const fetchStatus = useCallback(async () => {
    try {
      const r = await adminApi.pipelineStatus()
      setStatus(r.data)
    } catch {
      // ignore
    } finally {
      setLoadingStatus(false)
    }
  }, [])

  const fetchHistory = useCallback(async () => {
    try {
      const r = await adminApi.pipelineHistory(10)
      setHistory(r.data)
    } catch {
      // ignore
    }
  }, [])

  // Poll faster while a run is active
  useEffect(() => {
    fetchStatus()
    fetchHistory()

    const isRunning = status?.last_run?.status === 'running'
    const interval = isRunning ? 10_000 : 30_000

    pollRef.current = setInterval(() => {
      fetchStatus()
      fetchHistory()
    }, interval)

    return () => clearInterval(pollRef.current)
  }, [fetchStatus, fetchHistory, status?.last_run?.status])

  const handleRun = async (mode) => {
    setTriggering(mode)
    try {
      await adminApi.pipelineRun(mode)
      showToast(`Pipeline (${mode}) started — this runs in the background.`)
      setTimeout(() => { fetchStatus(); fetchHistory() }, 1500)
    } catch (err) {
      showToast(err.message ?? 'Failed to start pipeline', 'error')
    } finally {
      setTriggering(null)
    }
  }

  const handleRetrain = async () => {
    setTriggering('retrain')
    try {
      await adminApi.pipelineRetrain()
      showToast('Model retraining started — check status in a few minutes.')
      setTimeout(() => fetchStatus(), 2000)
    } catch (err) {
      showToast(err.message ?? 'Failed to start retraining', 'error')
    } finally {
      setTriggering(null)
    }
  }

  const lastRun = status?.last_run
  const isRunning = lastRun?.status === 'running'

  return (
    <div className="space-y-6">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
          toast.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {toast.msg}
        </div>
      )}

      <div>
        <h1 className="text-[32px] font-bold text-black leading-tight">Pipeline Control</h1>
        <p className="text-sm text-as-body mt-1">Scrape, sync, and retrain on demand or monitor scheduled runs</p>
      </div>

      {/* Status + Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Active Listings', value: status?.total_active?.toLocaleString() ?? '—' },
          { label: 'Sold (in DB)', value: status?.total_sold?.toLocaleString() ?? '—' },
          { label: 'Model R²', value: status?.model_r2 != null ? status.model_r2.toFixed(3) : '—' },
          { label: 'Model MAE', value: status?.model_mae != null ? `€${Math.round(status.model_mae).toLocaleString()}` : '—' },
        ].map(({ label, value }) => (
          <div key={label} className="card p-4">
            <p className="text-xs text-as-muted uppercase tracking-wider font-semibold mb-1">{label}</p>
            <p className="text-2xl font-bold text-black">{value}</p>
          </div>
        ))}
      </div>

      {/* Last run status */}
      <div className="card p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-black">Last Pipeline Run</h2>
          {isRunning && <span className="text-xs text-blue-600 font-medium animate-pulse">Running…</span>}
        </div>

        {loadingStatus ? (
          <p className="text-as-muted text-sm animate-pulse">Loading…</p>
        ) : lastRun ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-xs text-as-muted mb-0.5">Mode</p>
              <p className="font-medium capitalize">{lastRun.mode?.replace('_', ' ')}</p>
            </div>
            <div>
              <p className="text-xs text-as-muted mb-0.5">Status</p>
              <StatusBadge status={lastRun.status} />
            </div>
            <div>
              <p className="text-xs text-as-muted mb-0.5">Started</p>
              <p className="font-medium">{lastRun.started_at ? new Date(lastRun.started_at).toLocaleString() : '—'}</p>
            </div>
            <div>
              <p className="text-xs text-as-muted mb-0.5">Duration</p>
              <p className="font-medium">{duration(lastRun.started_at, lastRun.finished_at)}</p>
            </div>
            <div>
              <p className="text-xs text-as-muted mb-0.5">New Listings</p>
              <p className="font-medium">{lastRun.new_listings ?? 0}</p>
            </div>
            <div>
              <p className="text-xs text-as-muted mb-0.5">Retrained</p>
              <p className="font-medium">{lastRun.retrained ? 'Yes' : 'No'}</p>
            </div>
            {lastRun.new_r2 != null && (
              <div>
                <p className="text-xs text-as-muted mb-0.5">New R²</p>
                <p className="font-medium">{lastRun.new_r2.toFixed(3)}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-as-muted text-sm">No pipeline runs yet.</p>
        )}
      </div>

      {/* Actions */}
      <div className="card p-5 space-y-4">
        <h2 className="font-semibold text-black">Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button
            className="btn-primary py-2 px-5 disabled:opacity-50"
            disabled={!!triggering || isRunning}
            onClick={() => handleRun('daily')}
          >
            {triggering === 'daily' ? 'Starting…' : 'Run Daily Scrape'}
          </button>
          <button
            className="btn-secondary py-2 px-5 disabled:opacity-50"
            disabled={!!triggering || isRunning}
            onClick={() => handleRun('full_sweep')}
          >
            {triggering === 'full_sweep' ? 'Starting…' : 'Run Full Sweep'}
          </button>
          <button
            className="btn-secondary py-2 px-5 disabled:opacity-50"
            disabled={!!triggering || isRunning}
            onClick={handleRetrain}
          >
            {triggering === 'retrain' ? 'Starting…' : 'Force Retrain Model'}
          </button>
        </div>
        <p className="text-xs text-as-muted">
          Daily scrape: ~5–15 min, new listings only. Full sweep: ~30–60 min, detects sold listings too.
          Runs happen in the background — refresh status to see progress.
        </p>
      </div>

      {/* History */}
      <div className="card p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-[#f0f0f0]">
          <h2 className="font-semibold text-black">Run History</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-[#f9f9f9] border-b border-[#e8e8e8]">
              <tr>
                {['Mode', 'Status', 'Started', 'Duration', 'New', 'Retrained', 'R²'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-as-muted uppercase tracking-wider whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f0f0f0]">
              {history.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-as-muted">No runs yet</td></tr>
              ) : history.map(run => (
                <tr key={run.id} className="hover:bg-as-chip transition-colors">
                  <td className="px-4 py-3 font-medium capitalize">{run.mode?.replace('_', ' ')}</td>
                  <td className="px-4 py-3"><StatusBadge status={run.status} /></td>
                  <td className="px-4 py-3 text-as-muted whitespace-nowrap">{run.started_at ? new Date(run.started_at).toLocaleString() : '—'}</td>
                  <td className="px-4 py-3 whitespace-nowrap">{duration(run.started_at, run.finished_at)}</td>
                  <td className="px-4 py-3">{run.new_listings ?? 0}</td>
                  <td className="px-4 py-3">{run.retrained ? 'Yes' : '—'}</td>
                  <td className="px-4 py-3">{run.new_r2 != null ? run.new_r2.toFixed(3) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
