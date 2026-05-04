import { useMemo } from 'react'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import ChartPanel from './ChartPanel'
import MetricCard from './MetricCard'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend
)

const baseChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index',
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#020617',
      borderColor: '#334155',
      borderWidth: 1,
      titleColor: '#f8fafc',
      bodyColor: '#cbd5e1',
      displayColors: true,
    },
  },
  scales: {
    x: {
      border: { display: false },
      ticks: { color: '#94a3b8', maxRotation: 0 },
      grid: { color: 'rgba(148, 163, 184, 0.06)' },
    },
    y: {
      beginAtZero: true,
      border: { display: false },
      ticks: { color: '#94a3b8', precision: 0 },
      grid: { color: 'rgba(148, 163, 184, 0.12)' },
    },
  },
}

const numberFormatter = new Intl.NumberFormat('en-US')

const formatNumber = (value) => numberFormatter.format(Number(value ?? 0))

const formatPercent = (value) => `${value.toFixed(1)}%`

function MetricsOverview({ metrics, errorTrend }) {
  const throughput = metrics?.system_throughput ?? {}
  const errors = metrics?.error_analytics ?? {}
  const serviceInsights = metrics?.service_level_insights ?? {}
  const totalLogs = throughput.total_logs_processed ?? throughput.total_logs_received ?? 0
  const errorCount = errors.total_error_count ?? 0
  const errorRate = totalLogs > 0 ? (errorCount / totalLogs) * 100 : 0
  const queueDepth = throughput.queue_depth ?? 0

  const lineData = useMemo(
    () => ({
      labels: errorTrend.map((point) => point.time),
      datasets: [
        {
          label: 'Errors',
          data: errorTrend.map((point) => point.value),
          borderColor: '#f87171',
          backgroundColor: 'rgba(248, 113, 113, 0.08)',
          borderWidth: 2,
          fill: true,
          pointBackgroundColor: '#fca5a5',
          pointBorderColor: '#0f172a',
          pointHoverRadius: 4,
          pointRadius: 2,
          tension: 0.38,
        },
      ],
    }),
    [errorTrend]
  )

  const serviceEntries = useMemo(
    () =>
      Object.entries(serviceInsights.logs_per_service ?? {})
        .sort(([, a], [, b]) => b - a)
        .slice(0, 8),
    [serviceInsights.logs_per_service]
  )

  const barData = useMemo(
    () => ({
      labels: serviceEntries.length ? serviceEntries.map(([service]) => service) : ['No data'],
      datasets: [
        {
          label: 'Logs',
          data: serviceEntries.length ? serviceEntries.map(([, count]) => count) : [0],
          backgroundColor: 'rgba(45, 212, 191, 0.44)',
          borderColor: 'rgba(125, 211, 252, 0.75)',
          borderWidth: 1,
          borderRadius: 3,
          maxBarThickness: 34,
        },
      ],
    }),
    [serviceEntries]
  )

  return (
    <section id="metrics" className="grid grid-cols-1 gap-4 lg:grid-cols-12">
      <div className="lg:col-span-3">
        <MetricCard
          label="Total Logs"
          value={formatNumber(totalLogs)}
          helper={`${formatNumber(throughput.total_logs_received ?? 0)} received`}
          tone="normal"
        />
      </div>
      <div className="lg:col-span-3">
        <MetricCard label="Error Count" value={formatNumber(errorCount)} helper="Cumulative errors" tone="error" />
      </div>
      <div className="lg:col-span-3">
        <MetricCard
          label="Error Rate"
          value={formatPercent(errorRate)}
          helper={`${formatNumber(errors.current_window_error_count ?? 0)} in current window`}
          tone={errorRate > 0 ? 'error' : 'normal'}
        />
      </div>
      <div className="lg:col-span-3">
        <MetricCard
          label="Queue Depth"
          value={formatNumber(queueDepth)}
          helper={`${formatNumber(throughput.queue_rejections_total ?? 0)} rejected`}
          tone={queueDepth > 0 ? 'error' : 'normal'}
        />
      </div>

      <div className="lg:col-span-7">
        <ChartPanel title="Error Trend" subtitle="Current rolling error window">
          <Line data={lineData} options={baseChartOptions} />
        </ChartPanel>
      </div>
      <div className="lg:col-span-5">
        <ChartPanel title="Logs per Service" subtitle="Top services by processed volume">
          <Bar data={barData} options={baseChartOptions} />
        </ChartPanel>
      </div>
    </section>
  )
}

export default MetricsOverview
