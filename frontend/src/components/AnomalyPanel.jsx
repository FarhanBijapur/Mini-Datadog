function AnomalyPanel({ metrics }) {
  const anomaly = metrics?.anomaly_detection?.last_anomaly
  const active = metrics?.anomaly_detection?.anomaly_active
  const workerStatus = metrics?.system_throughput?.worker_status ?? 'stopped'
  const currentWindow = metrics?.error_analytics?.current_window_error_count ?? 0
  const previousWindow = metrics?.error_analytics?.previous_window_error_count ?? 0
  const ratio = previousWindow > 0 ? Math.min(100, Math.round((currentWindow / previousWindow) * 50)) : currentWindow > 0 ? 100 : 18

  return (
    <section className="rounded-lg border border-slate-800 bg-[#111827] shadow-lg shadow-black/25">
      <div className="flex items-start justify-between gap-4 border-b border-slate-800 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Anomaly Panel</h2>
          <p className="mt-1 text-xs text-gray-500">Rolling error-window signal</p>
        </div>
        <span
          className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
            active
              ? 'border-red-500/30 bg-red-500/10 text-red-300'
              : 'border-green-500/30 bg-green-500/10 text-green-300'
          }`}
        >
          {active ? 'Active' : 'Normal'}
        </span>
      </div>

      <div className="space-y-3 p-4 text-sm">
        <div className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-950 p-4">
          <div
            className="grid h-24 w-24 shrink-0 place-items-center rounded-full"
            style={{
              background: `conic-gradient(${active ? '#f87171' : '#34d399'} ${ratio}%, #1f2937 ${ratio}% 100%)`,
            }}
          >
            <div className="grid h-16 w-16 place-items-center rounded-full bg-[#111827]">
              <span className={active ? 'font-mono text-xl font-bold text-red-300' : 'font-mono text-xl font-bold text-green-300'}>
                {currentWindow}
              </span>
            </div>
          </div>
          <div className="min-w-0">
            <p className="text-xs uppercase text-gray-500">Error Pressure</p>
            <p className="mt-2 text-sm text-gray-300">
              {active ? 'Current window is elevated.' : 'No active anomaly detected.'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
            <p className="text-xs uppercase text-gray-500">Current Window</p>
            <p className="mt-2 text-2xl font-bold text-red-400">{currentWindow}</p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
            <p className="text-xs uppercase text-gray-500">Previous Window</p>
            <p className="mt-2 text-2xl font-bold text-gray-200">{previousWindow}</p>
          </div>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 p-3">
          <span className="text-gray-400">Worker Status</span>
          <span
            className={
              workerStatus === 'running'
                ? 'font-semibold text-green-400'
                : 'font-semibold text-red-400'
            }
          >
            {workerStatus}
          </span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
          <p className="mb-2 text-xs uppercase text-gray-500">Last Anomaly</p>
          <p className="text-sm text-white">
            {anomaly
              ? `Errors moved from ${anomaly.previous_count} to ${anomaly.current_count}`
              : 'No anomaly detected yet'}
          </p>
          <p className="mt-2 text-xs text-gray-500">
            {anomaly?.timestamp ?? 'timestamp unavailable'}
          </p>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 p-3">
          <span className="text-gray-400">Affected Service</span>
          <span className="font-semibold text-white">{anomaly?.affected_service ?? 'none'}</span>
        </div>
      </div>
    </section>
  )
}

export default AnomalyPanel
