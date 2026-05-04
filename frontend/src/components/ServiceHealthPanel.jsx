const numberFormatter = new Intl.NumberFormat('en-US')

function ServiceHealthPanel({ services, errorsByService }) {
  const maxLogs = Math.max(...services.map(([, count]) => count), 1)
  const rows = services.length ? services : [['no-service-data', 0]]

  return (
    <section className="rounded-lg border border-slate-800 bg-[#111827] shadow-lg shadow-black/25">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold text-white">Service Health</h2>
        <p className="mt-1 text-xs text-gray-500">Volume and error distribution</p>
      </div>

      <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
        {rows.slice(0, 6).map(([service, count]) => {
          const errors = errorsByService?.[service] ?? 0
          const width = Math.max(5, Math.round((count / maxLogs) * 100))
          const hasErrors = errors > 0

          return (
            <div key={service} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <div className="mb-1.5 flex items-center justify-between gap-3 text-xs">
                <span className="truncate font-medium text-gray-300">{service}</span>
                <span className={hasErrors ? 'font-mono text-red-300' : 'font-mono text-green-300'}>
                  {numberFormatter.format(count)}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-950">
                <div
                  className={hasErrors ? 'h-full rounded-full bg-red-400/80' : 'h-full rounded-full bg-cyan-300/70'}
                  style={{ width: `${width}%` }}
                />
              </div>
              <p className="mt-1 text-[11px] text-gray-500">
                {numberFormatter.format(errors)} errors
              </p>
            </div>
          )
        })}
      </div>
    </section>
  )
}

export default ServiceHealthPanel
