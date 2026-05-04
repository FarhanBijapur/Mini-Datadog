const navItems = ['Dashboard', 'Logs', 'Metrics']

function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-56 border-r border-slate-800 bg-[#070b11] px-3 py-4 text-white shadow-2xl shadow-black/40 lg:flex lg:flex-col">
      <div className="border-b border-slate-900 px-2 pb-4">
        <p className="text-[10px] font-semibold uppercase text-gray-500">Mini Datadog</p>
        <h1 className="mt-1 text-base font-bold">Observability</h1>
      </div>

      <nav className="mt-4 space-y-1">
        {navItems.map((item) => {
          const isActive = item === 'Dashboard'
          return (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? 'border border-slate-700 bg-slate-900 text-white'
                  : 'text-gray-400 hover:bg-slate-900 hover:text-white'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  isActive ? 'bg-green-400' : 'bg-slate-600'
                }`}
              />
              {item}
            </a>
          )
        })}
      </nav>

      <div className="mt-auto rounded-lg border border-slate-900 bg-slate-950 p-3">
        <p className="text-[10px] uppercase text-gray-500">Environment</p>
        <p className="mt-2 text-sm font-semibold text-white">Localhost</p>
        <p className="mt-1 text-xs text-gray-400">API http://localhost:8000</p>
      </div>
    </aside>
  )
}

export default Sidebar
