const STAGES = [
  { icon: '🧠', label: 'Understanding your request' },
  { icon: '🏬', label: 'Selecting stores' },
  { icon: '🔗', label: 'Comparing products' },
  { icon: '⚖️', label: 'Ranking deals' },
]

export default function LoadingStages({ activeStage }: { activeStage: number }) {
  return (
    <div className="w-full max-w-2xl animate-[fadeIn_0.3s_ease-out] rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg backdrop-blur">
      <ul className="space-y-3">
        {STAGES.map((stage, index) => {
          const isDone = index < activeStage
          const isActive = index === activeStage
          return (
            <li key={stage.label} className="flex items-center gap-3 text-sm">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors duration-500 ${
                  isDone
                    ? 'bg-emerald-400 text-slate-900'
                    : isActive
                      ? 'bg-sky-400 text-slate-900 animate-pulse'
                      : 'bg-white/10 text-slate-400'
                }`}
              >
                {isDone ? '✓' : <span aria-hidden="true">{stage.icon}</span>}
              </span>
              <span
                className={`transition-colors duration-500 ${
                  isActive ? 'font-semibold text-white' : isDone ? 'text-slate-300' : 'text-slate-500'
                }`}
              >
                {stage.label}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
