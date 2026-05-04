const toneStyles = {
  normal: {
    value: 'text-green-400',
    indicator: 'bg-green-400 shadow-green-400/30',
    helper: 'text-green-300',
  },
  error: {
    value: 'text-red-400',
    indicator: 'bg-red-400 shadow-red-400/30',
    helper: 'text-red-300',
  },
  neutral: {
    value: 'text-white',
    indicator: 'bg-slate-400 shadow-slate-400/20',
    helper: 'text-gray-400',
  },
}

function MetricCard({ label, value, helper, tone = 'normal' }) {
  const styles = toneStyles[tone] ?? toneStyles.neutral

  return (
    <article className="rounded-lg border border-slate-800 bg-[#111827] p-3 shadow-lg shadow-black/25">
      <div className="flex items-start justify-between gap-4">
        <p className="text-xs font-semibold uppercase text-gray-500">{label}</p>
        <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full shadow-lg ${styles.indicator}`} />
      </div>
      <p className={`mt-2 font-mono text-3xl font-bold tracking-normal ${styles.value}`}>{value}</p>
      {helper && <p className={`mt-1 text-xs ${styles.helper}`}>{helper}</p>}
    </article>
  )
}

export default MetricCard
