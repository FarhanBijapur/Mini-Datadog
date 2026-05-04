import { useCallback, useEffect, useState } from 'react'
import AnomalyPanel from './components/AnomalyPanel'
import MetricsOverview from './components/MetricsOverview'
import RecentLogsTable from './components/RecentLogsTable'
import Sidebar from './components/Sidebar'
import { fetchLogs, fetchMetrics } from './services/api'

const normalizeLogs = (payload) => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.logs)) return payload.logs
  if (Array.isArray(payload?.items)) return payload.items
  if (Array.isArray(payload?.data)) return payload.data
  return []
}

const getLogsEndpointUnavailable = (error) => {
  const status = error?.response?.status
  return status === 404 || status === 405
}

function App() {
  const [metrics, setMetrics] = useState(null)
  const [logs, setLogs] = useState([])
  const [errorTrend, setErrorTrend] = useState([])
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [metricsError, setMetricsError] = useState('')
  const [logsAvailable, setLogsAvailable] = useState(true)

  const loadDashboard = useCallback(async () => {
    const metricsRequest = fetchMetrics()
    const logsRequest = logsAvailable ? fetchLogs() : Promise.resolve([])
    const [metricsResult, logsResult] = await Promise.allSettled([metricsRequest, logsRequest])

    if (metricsResult.status === 'fulfilled') {
      const data = metricsResult.value
      const currentWindowErrorCount = data?.error_analytics?.current_window_error_count ?? 0

      setMetrics(data)
      setMetricsError('')
      setLastUpdated(new Date())
      setErrorTrend((history) => [
        ...history.slice(-17),
        {
          time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }),
          value: currentWindowErrorCount,
        },
      ])
    } else {
      setMetricsError('Metrics endpoint unavailable')
    }

    if (logsResult.status === 'fulfilled') {
      setLogs(normalizeLogs(logsResult.value))
    } else if (getLogsEndpointUnavailable(logsResult.reason)) {
      setLogsAvailable(false)
      setLogs([])
    }

    setIsInitialLoading(false)
  }, [logsAvailable])

  useEffect(() => {
    const initialLoadId = setTimeout(loadDashboard, 0)
    const intervalId = setInterval(loadDashboard, 3000)
    return () => {
      clearTimeout(initialLoadId)
      clearInterval(intervalId)
    }
  }, [loadDashboard])

  const isOffline = !metrics || !logsAvailable

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <Sidebar />

      <main id="dashboard" className="min-h-screen lg:pl-56">
        <div className="mx-auto max-w-[1500px] px-3 py-3 sm:px-5 lg:px-5">
          <header className="mb-3 rounded-lg border border-slate-800 bg-[#0b111a] px-4 py-3 shadow-lg shadow-black/20">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase text-gray-500 lg:hidden">Mini Datadog</p>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span>Dashboards</span>
                <span>/</span>
                <span className="text-gray-300">Production Overview</span>
              </div>
              <h1 className="mt-1 text-xl font-semibold text-white">Observability Dashboard</h1>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-sm">
              {metricsError && (
                <span className="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 font-medium text-red-300">
                  API offline
                </span>
              )}
              <span
                className={`rounded-full border px-3 py-1 font-medium ${
                  metricsError
                    ? 'border-slate-700 bg-slate-950 text-gray-400'
                    : 'border-green-500/30 bg-green-500/10 text-green-300'
                }`}
              >
                {metricsError ? 'Disconnected' : 'Live'}
              </span>
              <span className="text-gray-400">
                Updated {lastUpdated ? lastUpdated.toLocaleTimeString() : '--'}
              </span>
            </div>
            </div>
          </header>

          <div className="grid grid-cols-1 gap-3 xl:grid-cols-12">
            <div className="xl:col-span-12">
              <MetricsOverview metrics={metrics} errorTrend={errorTrend} />
            </div>

            <div className="xl:col-span-8">
              <RecentLogsTable
                logs={logs}
                isLoading={isInitialLoading}
                isOffline={isOffline}
              />
            </div>

            <div className="xl:col-span-4">
              <AnomalyPanel metrics={metrics} />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
