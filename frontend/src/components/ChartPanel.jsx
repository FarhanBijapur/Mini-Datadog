function ChartPanel({ title, subtitle, children }) {
  return (
    <section className="rounded-lg border border-slate-800 bg-[#111827] shadow-lg shadow-black/25">
      <div className="flex items-start justify-between gap-4 border-b border-slate-800 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-white">{title}</h2>
          {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
        </div>
        <span className="mt-1 h-2 w-2 rounded-full bg-cyan-300/80" />
      </div>
      <div className="h-56 px-3 pb-4 pt-3">
        {children}
      </div>
    </section>
  )
}

export default ChartPanel
