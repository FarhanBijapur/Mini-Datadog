const levelClasses = {
  ERROR: 'border-red-500/30 bg-red-500/10 text-red-300',
  WARN: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
  INFO: 'border-sky-400/25 bg-sky-400/10 text-sky-200',
  DEBUG: 'border-slate-500/30 bg-slate-500/10 text-gray-300',
}

const formatTimestamp = (value) => {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const getMessage = (log) => {
  if (log.message) return log.message
  if (log.body) return log.body
  if (log.event) return log.event
  return 'No message'
}

function RecentLogsTable({ logs, isLoading, isOffline }) {
  const rows = logs.slice(0, 50)

  return (
    <section id="logs" className="rounded-lg border border-slate-800 bg-[#111827] shadow-lg shadow-black/25">
      <div className="flex items-center justify-between gap-4 border-b border-slate-800 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Recent Logs</h2>
          <p className="mt-1 text-xs text-gray-500">
            {isOffline ? 'Waiting for /logs endpoint' : `${rows.length} events in view`}
          </p>
        </div>
        <span
          className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
            isOffline
              ? 'border-slate-700 bg-slate-950 text-gray-400'
              : 'border-green-500/30 bg-green-500/10 text-green-300'
          }`}
        >
          {isOffline ? 'Offline' : 'Live'}
        </span>
      </div>

      <div className="max-h-80 overflow-auto">
        <table className="min-w-full table-fixed text-left text-xs">
          <thead className="sticky top-0 z-10 border-b border-slate-800 bg-[#111827] uppercase text-gray-500">
            <tr>
              <th className="w-28 px-4 py-2.5 font-semibold">Time</th>
              <th className="w-24 px-4 py-2.5 font-semibold">Level</th>
              <th className="w-44 px-4 py-2.5 font-semibold">Service</th>
              <th className="px-4 py-2.5 font-semibold">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((log, index) => {
              const level = String(log.level ?? log.severity ?? 'INFO').toUpperCase()
              const timestamp = log.timestamp ?? log.processed_at ?? log.received_at

              return (
                <tr key={log.id ?? log.trace_id ?? `${timestamp}-${index}`} className="bg-[#111827] hover:bg-slate-900/70">
                  <td className="whitespace-nowrap px-4 py-2.5 font-mono text-gray-500">{formatTimestamp(timestamp)}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex min-w-16 justify-center rounded-full border px-2.5 py-1 text-xs font-semibold ${
                        levelClasses[level] ?? levelClasses.INFO
                      }`}
                    >
                      {level}
                    </span>
                  </td>
                  <td className="truncate px-4 py-2.5 font-medium text-gray-200">
                    {log.service ?? log.source ?? 'unknown'}
                  </td>
                  <td className="truncate px-4 py-2.5 text-gray-300">{getMessage(log)}</td>
                </tr>
              )
            })}

            {!rows.length && (
              <tr>
                <td className="px-4 py-10 text-center text-gray-400" colSpan="4">
                  {isLoading ? 'Loading log stream...' : 'No recent logs returned.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default RecentLogsTable
